import pandas as pd
from flask import Flask, render_template, request
import math
import webbrowser
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os

app = Flask(__name__)

# Sample dataset for demonstration
# Replace this with your dynamic dataset loading logic
DATASET_PATH = os.path.join(os.getcwd(), 'dataset.csv')



def replace_newline_with_br(text):
    return text.replace('\n', '<br>')

app.jinja_env.filters['replace_newline_with_br'] = replace_newline_with_br



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visualization/<int:page>')
def visualization(page=1):
    rows_per_page = 10
    start_index = (page - 1) * rows_per_page
    end_index = start_index + rows_per_page
    sample_dataset = pd.read_csv(DATASET_PATH, nrows=page*20)
    # sample_dataset['Before Bug fix'] = sample_dataset['Before Bug fix'].replace("\n", "<br>", regex=True)
    # sample_dataset['After Bug fix'] = sample_dataset['After Bug fix'].replace("\n", "<br>", regex=True)
    # sample_dataset['Location'] = sample_dataset['Location'].replace("\n", "<br>", regex=True)
    subset_data = sample_dataset.iloc[start_index:end_index]
    
    return render_template('visualization.html', data=subset_data, columns=subset_data.columns, current_page=page, total_pages=math.ceil(len(sample_dataset) / rows_per_page))

@app.route('/quantitative', methods=['GET', 'POST'])
def quantitative():
    if request.method == 'POST':
        dropdown1_value = request.form['dropdown1']
        dropdown2_value = request.form['dropdown2']
        rows = int(request.form['num_rows'])

        sample_dataset = pd.read_csv(DATASET_PATH, nrows = rows)
        # Process the selected options and get the data for the chart
        chart_data = process_chart_data(sample_dataset, dropdown1_value, dropdown2_value)

        # Generate a base64-encoded image from the Matplotlib plot
        img_uri = generate_plot(chart_data, dropdown1_value, dropdown2_value)

        return render_template('quantitative.html', img_uri=img_uri)

    return render_template('quantitative.html', img_uri=None)

def process_chart_data(sample_dataset, option1, option2):
    # Sample processing logic
    # Replace this with your actual data processing logic based on selected options
    # Extract x and y values for the plot
    x_values = list(range(len(sample_dataset)))
    print(option1)
    if option1 == 'Similarity Score':
        y_values = sample_dataset['crystalBLEU_score'].tolist()
    else:
        y_values= ((sample_dataset[option1]-sample_dataset[option1].min())/(sample_dataset[option1].max()-sample_dataset[option1].min())).tolist()

    return {'x_values': x_values, 'y_values': y_values}

def generate_plot(chart_data, y, x):
    plt.plot(chart_data['x_values'], chart_data['y_values'])
    plt.xlabel(x)  # Label for x-axis
    plt.ylabel(y)  # Label for y-axis
    plt.title(f'Quantitative Analysis for {y} vs {x}')  # Plot title
    plt.grid(True)

    # Save the plot to a BytesIO object
    img_bytesio = BytesIO()
    plt.savefig(img_bytesio, format='png')
    img_bytesio.seek(0)

    # Encode the plot image in base64
    img_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')

    plt.close()  # Close the plot to free up resources

    return f'data:image/png;base64,{img_uri}'

# if __name__ == '__main__':
#     webbrowser.open('http://127.0.0.1:5000')
#     app.run(debug=True)