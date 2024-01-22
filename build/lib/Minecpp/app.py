import pandas as pd
from flask import Flask, render_template, request
import math
import webbrowser
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import threading
import signal
import sys
from pprint import pformat


app = Flask(__name__)

# Sample dataset for demonstration
# Replace this with your dynamic dataset loading logic
DATASET_PATH = os.path.join(os.getcwd(), 'dataset.csv')

def pretty_print_dict(d):
    formatted_dict = pformat(d, width=10000)  # Adjust the width value as needed
    # Replace commas with line breaks
    formatted_dict = formatted_dict.replace(', ', ',\n')
    formatted_dict = formatted_dict.replace('\\', '')
    # Remove the outer curly braces from the pformat output
    formatted_dict = formatted_dict[1:-1]
    print(formatted_dict)
    return formatted_dict

app.jinja_env.filters['pretty_print_dict'] = pretty_print_dict


def replace_newline_with_br(text):
    return text.replace('\n', '<br>')

app.jinja_env.filters['replace_newline_with_br'] = replace_newline_with_br

def tensor2flt(tensor):
    tensor=tensor.strip(' tensor([')
    tensor=tensor.rstrip('])')
    return round(float(tensor),3)

app.jinja_env.filters['tensor2float'] = tensor2flt



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/exit_app')
def exit_app():
    return render_template('exit.html')

@app.route('/confirmed_exit')
def confirmed_exit():
    # Perform cleanup or additional actions before exiting

    # Stop the Flask server (requires threading to avoid blocking the main thread)
    thread = threading.Thread(target=shutdown_server)
    thread.start()

    return 'Exiting...'

def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)
    sys.exit()

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
        rows = int(request.form['num_rows'])

        sample_dataset = pd.read_csv(DATASET_PATH, nrows=rows)
        chart_data = process_chart_data(sample_dataset)
        img_uri1, img_uri2 = generate_plot(chart_data)

        return render_template('quantitative.html', img_uri1=img_uri1, img_uri2 = img_uri2)

    return render_template('quantitative.html', img_uri1=None, img_uri2 = None)

def process_chart_data(sample_dataset):
    x_values = list(range(len(sample_dataset)))
    
    y_values_coding_effort = ((sample_dataset['Coding Effort'] - sample_dataset['Coding Effort'].min()) /
                              (sample_dataset['Coding Effort'].max() - sample_dataset['Coding Effort'].min())).tolist()

    y_values_crystalBLEU = sample_dataset['crystalBLEU_score'].round(3).tolist()
    y_values_BLEU = sample_dataset['BLEU'].round(3).tolist()

    extract_index_2 = lambda x: round(float(x.split(', ')[2].lstrip(' tensor([').rstrip(')]')),3)
    y_values_bert_score = sample_dataset['bert_score'].apply(extract_index_2).tolist()

    return {'x_values': x_values,
            'y_values_coding_effort': y_values_coding_effort,
            'y_values_crystalBLEU': y_values_crystalBLEU,
            'y_values_BLEU': y_values_BLEU,
            'y_values_bert_score': y_values_bert_score}

def generate_plot(chart_data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    # Plot 1: Coding Effort
    ax1.plot(chart_data['x_values'], chart_data['y_values_coding_effort'])
    ax1.set_title('Coding Effort')
    ax1.set_xlabel('Bug-fix pairs')
    ax1.set_ylabel('Normalized Coding Effort')

    # Save the plot to a BytesIO object
    img_bytesio1 = BytesIO()
    plt.savefig(img_bytesio1, format='png')
    img_bytesio1.seek(0)

    # Encode the plot image in base64
    img_uri1 = base64.b64encode(img_bytesio1.getvalue()).decode('utf-8')

    # Clear the figure for the next plot
    # plt.clf()

    # Plot 2: Similarity Scores
    ax2.plot(chart_data['x_values'], chart_data['y_values_crystalBLEU'], label='crystalBLEU')
    ax2.plot(chart_data['x_values'], chart_data['y_values_BLEU'], label='BLEU')
    ax2.plot(chart_data['x_values'], chart_data['y_values_bert_score'], label='bert_score')
    ax2.set_title('Similarity Scores')
    ax2.set_xlabel('Bug-fix pairs')
    ax2.set_ylabel('Similarity Scores')
    ax2.legend()

    # Save the plot to a BytesIO object
    img_bytesio2 = BytesIO()
    plt.savefig(img_bytesio2, format='png')
    img_bytesio2.seek(0)

    # Encode the plot image in base64
    img_uri2 = base64.b64encode(img_bytesio2.getvalue()).decode('utf-8')

    plt.close()  # Close the plot to free up resources

    return f'data:image/png;base64,{img_uri1}', f'data:image/png;base64,{img_uri2}'

# if __name__ == '__main__':
#     webbrowser.open('http://127.0.0.1:5000')
#     app.run(debug=True)