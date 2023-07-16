import requests
import pymongo
import json
import hmac  # Library for HMAC-based authentication
import datetime  # Library for creating delays
from time import sleep  # Function for adding delays between requests
import hashlib  # Library for hashing
from pandas import read_csv
import concurrent.futures
import time


"""#################################################################################"""
"""                            MoodysData Class                                     """
"""#################################################################################"""
"""
@desc <description of the class>
"""
class GetMoodysData(object):
    """
    @desc constructor initiate values for variables/attributes.
    @param accKey{string}: Access key for API authentication.
    @param encKey{string}: Encryption key for API authentication.
    @param BASKET_NAME{<type>}: <decription of BASKET_NAME>. Default is None.
    """
    def __init__(self, accKey, encKey):
        self.accKey = accKey  # Access key for API authentication
        self.encKey = encKey  # Encryption key for API authentication        

    """
    @desc Function for making API requests.
    @param apiCommand{string}: <decription of apiCommand>.
    @param accKey{string}: Access key for API authentication. [Is NOT being used]
    @param encKey{string}: Encryption key for API authentication. [Is NOT being used]
    @param call_type{string}: <decription of call_type>. Default is "GET".
    @param params{<type>}: <decription of params>. Default is None.
    @return response{request}: <description response>.
    """
    """If you are not gonna used accKey and encKey I would remove it"""
    def api_call(self, apiCommand, accKey, encKey, call_type="GET", params=None):
        url = "https://api.economy.com/data/v1/" + apiCommand
        timeStamp = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%SZ")
        payload = bytes(self.accKey + timeStamp, "utf-8")
        signature = hmac.new(bytes(self.encKey, "utf-8"), payload, digestmod=hashlib.sha256)
        head = {
            "AccessKeyId": self.accKey,
            "Signature": signature.hexdigest(),
            "TimeStamp": timeStamp,
        }
        sleep(1)
        if call_type == "POST":
            response = requests.post(url, headers=head, params=params)
        elif call_type == "DELETE":
            response = requests.delete(url, headers=head, params=params)
        else:
            response = requests.get(url, headers=head, params=params)
        return response

    """
    @desc retrieve multi-series data
    @param mnemonic_list{list}: <decription of mnemonic_list>.
    @param freq{<type>}: <decription of freq>. Default is None.
    @param trans{<type>}: <decription of trans>. Default is None.
    @param conv{<type>}: <decription of conv>. Default is None.
    @param startDate{<type>}: <decription of startDate>. Default is None.
    @param endDate{<type>}: <decription of endDate>. Default is None.
    @param vintage{<type>}: <decription of vintage>. Default is None.
    @param vintageVersion{<type>}: <decription of vintageVersion>. Default is None.
    @return results{list}: <description results>.
    """

    def retrieveMultiSeries(self, mnemonic_list, freq=None, trans=None, conv=None, startDate=None, endDate=None, vintage=None, vintageVersion=None):
        mnemonic_count = len(mnemonic_list)
        results = []

        batch_size = 25  # Adjust the batch size as per your requirements

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create a list of futures for parallel API calls
            futures = []
            for i in range(0, mnemonic_count, batch_size):
                batch_mnemonics = mnemonic_list[i:i + batch_size]
                future = executor.submit(self.retrieveMultiSeriesBatch, batch_mnemonics, freq, trans, conv, startDate, endDate, vintage, vintageVersion)
                futures.append(future)

            # Wait for all futures to complete and collect the results
            for future in concurrent.futures.as_completed(futures):
                data = future.result()
                results.extend(data['data'])

        return results
    

    """
    @desc retrieve multi-series data for a batch of mnemonics
    @param mnemonic_list{list}: <decription of mnemonic_list>.
    @param freq{<type>}: <decription of freq>. Default is None.
    @param trans{<type>}: <decription of trans>. Default is None.
    @param conv{<type>}: <decription of conv>. Default is None.
    @param startDate{<type>}: <decription of startDate>. Default is None.
    @param endDate{<type>}: <decription of endDate>. Default is None.
    @param vintage{<type>}: <decription of vintage>. Default is None.
    @param vintageVersion{<type>}: <decription of vintageVersion>. Default is None.
    @return data{json}: <description data>.
    """
    def retrieveMultiSeriesBatch(self, mnemonic_list, freq=None, trans=None, conv=None, startDate=None, endDate=None, vintage=None, vintageVersion=None):
        mnemonic_param = ';'.join(mnemonic_list)
        params = {'m': mnemonic_param}

        if freq:
            params['freq'] = freq
        if trans:
            params['trans'] = trans
        if conv:
            params['conv'] = conv
        if startDate:
            params['startDate'] = startDate
        if endDate:
            params['endDate'] = endDate
        if vintage:
            params['vintage'] = vintage
        if vintageVersion:
            params['vintageVersion'] = vintageVersion

        response = self.api_call('multi-series', self.accKey, self.encKey, params=params)
        data = response.json()
        return data
    
