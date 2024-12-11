from flask import Flask, request, jsonify
import requests
import mwparserfromhell

app = Flask(__name__)

def get_page_id(title):
    query = f"{title} book"
    url = f'https://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch={query}&formatversion=2'
    response = requests.get(url)
    data = response.json()
    if 'query' in data and 'search' in data['query']:
        return data['query']['search'][0]['pageid']
    return None

def get_infobox_content(page_id):
    url = f'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&pageids={page_id}&rvprop=content&formatversion=2'
    response = requests.get(url)
    data = response.json()
    page_content = data['query']['pages'][0]['revisions'][0]['content']
    
    # Parse the wikitext content
    wikicode = mwparserfromhell.parse(page_content)
    templates = wikicode.filter_templates()
    
    # Find the infobox template
    infobox = None
    for template in templates:
        if template.name.matches("Infobox book"):
            infobox = template
            break
    
    # Extract data
    if infobox:
        infobox_data = {
            'title': infobox.get('name').value.strip_code().strip() if infobox.has('name') else None,
            'author': infobox.get('author').value.strip_code().strip() if infobox.has('author') else None,
            'publication_place': infobox.get('country').value.strip_code().strip() if infobox.has('country') else None,
            'publication_date': infobox.get('release_date').value.strip_code().strip() if infobox.has('release_date') else None,
            'genre': infobox.get('genre').value.strip_code().strip() if infobox.has('genre') else None,
        }
        return infobox_data
    else:
        return None

@app.route('/')
def home():
    return 'Hello World'

@app.route('/search', methods=['GET'])
def search():
    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Title parameter is required'}), 400

    page_id = get_page_id(title)
    if page_id:
        infobox_data = get_infobox_content(page_id)
        if infobox_data:
            return jsonify(infobox_data), 200
        else:
            return jsonify({'error': 'Infobox not found'}), 404
    else:
        return jsonify({'error': 'Page ID not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
