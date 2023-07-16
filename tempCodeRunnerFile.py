
@app.route('/analyze_data', methods=['GET','POST'])
def analyze_data_page():
    if request.method == 'POST':
        mnemonic = request.form.get('mnemonic')

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
            return render_template('analyze_data.html', error_message='Mnemonic not found.')

    # If it's a GET request, simply render the analyze data page without data
    return render_template('analyze_data.html', mnemonic=None, error_message=None)




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
