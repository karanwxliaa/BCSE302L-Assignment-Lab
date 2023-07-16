# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from api import GetMoodysData
from pandas import read_csv
import pymongo
import concurrent.futures
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import io
import base64
import datetime

app = Flask(__name__, template_folder=r'C:\Users\KARAN\Desktop\assurant\Moody-Automated-ETL\DBMS\templates')

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            return redirect(url_for('homepage'))
        else:
            return render_template('login.html', message='Invalid credentials.')
    return render_template('login.html', message='')

@app.route('/homepage')
def homepage():
    return render_template('homepage.html')



# New route for handling the search time series functionality
@app.route('/search_time_series')
def search_time_series():
    return render_template('search_time_series.html')

# New route for handling the search request
@app.route('/search', methods=['POST'])
def search():
    mnemonic = request.form.get('mnemonic')

    client = pymongo.MongoClient('mongodb://localhost:27017')
    database = client['GUI']
    collection = database['1kmn']

    result = collection.find_one({'_id': mnemonic})
    client.close()

    if result:
        return jsonify({'exists': True, 'series_data': result['series_data']})
    else:
        return jsonify({'exists': False})


@app.route('/input', methods=['GET', 'POST'])
def input_data():
    if request.method == 'POST':
        global mnemonic 
        mnemonic = request.form.get('mnemonic')
        return redirect(url_for('analyze_data_page', mnemonic=mnemonic))

    return render_template('input.html')


@app.route('/analyze_data', methods=['GET', 'POST'])
def analyze_data_page():
    if request.method == 'POST':
        # In case someone tries to post directly to this route
        return redirect(url_for('input_data'))

    global mnemonic
    if not mnemonic:
        return redirect(url_for('input_data'))

    client = pymongo.MongoClient('mongodb://localhost:27017')
    database = client['GUI']
    collection = database['1kmn']

    result = collection.find_one({'_id': mnemonic})
    client.close()

    if result:
        series_data = result['series_data']
        data_array = series_data.get('data', [])

        if not data_array:
            return render_template('analyze_data.html', mnemonic=mnemonic, error_message='No data found for the mnemonic.')

        client = pymongo.MongoClient('mongodb://localhost:27017')
        database = client['GUI']
        collection = database['1kmn']

        result = collection.find_one({'_id': mnemonic})
        client.close()

        if result:
            series_data = result['series_data']
            data_array = series_data.get('data', [])

            if not data_array:
                return render_template('analyze_data.html', error_message='No data found for the mnemonic.')

            # Extract dates and values from the data array
            dates = [datetime.datetime.strptime(item['date'], '%Y-%m-%d') for item in data_array]
            values = [item['value'] for item in data_array]

            # Convert values to a numpy array for further processing
            data_np_array = np.array(values)

            # Calculate mean and standard deviation
            mean_value = np.mean(data_np_array)
            std_dev_min = np.min(data_np_array)
            std_dev_max = np.max(data_np_array)

            # Plot the charts and get the image data
            line_plot_img = get_line_plot_image(dates, values)
            histogram_img = get_histogram_image(data_np_array)
            box_plot_img = get_box_plot_image(data_np_array)
            autocorrelation_plot_img = get_autocorrelation_plot_image(data_np_array)

        return render_template('analyze_data.html', mnemonic=mnemonic, line_plot_img=line_plot_img,
                               histogram_img=histogram_img, box_plot_img=box_plot_img,
                               autocorrelation_plot_img=autocorrelation_plot_img, mean_value=mean_value,
                               std_dev_min=std_dev_min, std_dev_max=std_dev_max)
    else:
        return render_template('analyze_data.html', mnemonic=mnemonic, error_message='Mnemonic not found.')



# Helper function to plot the line chart
def get_line_plot_image(dates, values):
    plt.figure()
    plt.plot(dates, values)
    plt.title('Time Series - Line Plot')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.xticks(rotation=45)

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    # Convert the plot to a base64 encoded string
    line_plot_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return line_plot_img

# Helper function to plot the histogram
def get_histogram_image(data_array):
    plt.figure()
    plt.hist(data_array, bins=20, alpha=0.7)
    plt.title('Histogram')
    plt.xlabel('Value')
    plt.ylabel('Frequency')

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    # Convert the plot to a base64 encoded string
    histogram_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return histogram_img


# Helper function to plot the boxplot
def get_box_plot_image(data_array):
    plt.figure()
    plt.boxplot(data_array)
    plt.title('Box Plot')
    plt.ylabel('Value')

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    # Convert the plot to a base64 encoded string
    box_plot_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return box_plot_img


# Helper function to plot the autocorrelation plot
def get_autocorrelation_plot_image(data_array):
    plt.figure()
    plt.acorr(data_array, maxlags=len(data_array) - 1)
    plt.title('Autocorrelation Plot')
    plt.xlabel('Lag')
    plt.ylabel('Autocorrelation')

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)

    # Convert the plot to a base64 encoded string
    autocorrelation_plot_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return autocorrelation_plot_img


@app.route('/add_data')
def add_data_page():
    return render_template('add_data.html')

# Route for handling the form submission on the "Add Data" page
@app.route('/add_data', methods=['POST'])
def add_data():
    # ... (your existing code for handling form data and adding it to the database)
    # Keep the existing "add_data" route logic here
    try:
        _id = request.form.get('_id')
        mnemonic = request.form.get('mnemonic')
        data = request.form.get('data')

        # Connect to MongoDB
        client = pymongo.MongoClient('mongodb://localhost:27017')
        database = client['GUI']
        collection = database['1kmn']

        # Prepare the document
        document = {'_id': _id, 'series_data': {'mnemonic': mnemonic, 'data': data}}

        # Insert the document into the database
        collection.insert_one(document)

        # Close the connection
        client.close()

        return jsonify({"message": "Data added successfully!"})

    except Exception as e:
        # Log the exact error
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500




@app.route('/retrieve_data', methods=['POST'])
def retrieve_data():
    try:
        # Get the number of mnemonics to retrieve from the frontend
        data = request.get_json()
        num_mnemonics = data.get('numMnemonics')  # Corrected key to 'numMnemonics'

        print("num_mnemonics:", num_mnemonics)


        # Read the mnemonic list from the CSV file
        # Getting the mnemonic list ready to call the API
        df = read_csv(r'C:\Users\KARAN\Desktop\assurant\Moody-Automated-ETL\Assurant_fullMnemonicList_20220510.csv', header=0, sep="|")
        mn_list = df['mnemonic'].tolist()
        mn_list[0] = mn_list[0][1:]
        # mn_list = mn_list[0:10000]  # Reducing the list to 10 mnemonics for testing

        # Slice the mnemonic list based on the given number
        mn_list = mn_list[:int(num_mnemonics)]
        print("Input = ",num_mnemonics)

        ACC_KEY = ""
        ENC_KEY = ""

        with concurrent.futures.ThreadPoolExecutor() as executor:
            num_threads = executor._max_workers

        print(f"\nNumber of threads: {num_threads}")
        
        # Initialize GetMoodysData with your API keys
        constructor = GetMoodysData(accKey=ACC_KEY, encKey=ENC_KEY)

        start_time = time.time()
        data = constructor.retrieveMultiSeries(mn_list)
        end_time = time.time()

        elapsed_time = end_time - start_time

        print(f"\nTotal time for {len(mn_list)} mnemonics : {elapsed_time} seconds")
        print(f"\nTotal time for 1619314 mnemonics : {((elapsed_time*1619314)/len(mn_list))/3600} hours")


        #Checking errors
        count, count_n = 0, 0
        for i in data:
            if i.get('error') == 'Series Not Found':
                count_n += 1
            else:
                count += 1
        print('Total mnemonics retrieved:', count)
        print('Total mnemonics not found:', count_n)


        #STORING IN MONGODB
        client = pymongo.MongoClient('mongodb://localhost:27017')
        database = client['GUI']
        collection = database['1kmn']
        c=0
        documents = []
        for series in data:
            mnemonic = series['mnemonic']
            series_json = series
            document = {'_id': mnemonic, 'series_data': series_json}
            documents.append(document)

        if documents:
            collection.insert_many(documents)

            

        client.close()

        return jsonify({"message": "Data Retrieval Successful!"})

    except Exception as e:
        # Log the exact error
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500




    


if __name__ == "__main__":
    app.run(debug=True, port=7777)






