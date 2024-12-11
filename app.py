from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def search_wikipedia(title):
    query = f"{title} book"
    url = f'https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={query}&formatversion=2'
    response = requests.get(url)
    # return first page id of search
    data = response.json()
    if 'query' in data and 'search' in data['query']:
        return data['query']['search'][0]['pageid']

    return response.json()

@app.route('/')
def home():
    return 'Hello World'

@app.route('/search', methods=['GET'])
def get_books():
    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Title parameter is required'}), 400

    search_result = search_wikipedia(title)
    return jsonify(search_result), 200

if __name__ == '__main__':
    app.run(debug=True)
