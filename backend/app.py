from flask import Flask, request, jsonify
import requests
import mwparserfromhell
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS
import os
from dotenv import load_dotenv
import re

app = Flask(__name__)
CORS(app)

# Load environment variables from .env file
load_dotenv()

# SQLite database configuration
DATABASE_URI = 'sqlite:///books.db'
engine = create_engine(DATABASE_URI)
Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    publication_place = Column(String)
    publication_date = Column(String)
    genre = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

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
            'publication_date': extract_first_year(infobox.get('release_date').value.strip_code().strip()) if infobox.has('release_date') else None,
            'genre': infobox.get('genre').value.strip_code().strip() if infobox.has('genre') else None,
        }
        return infobox_data
    else:
        return None

def extract_first_year(date_string):
    # Find the first four-digit number in the string
    match = re.search(r'\b\d{4}\b', date_string)
    if match:
        return match.group(0)
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
            new_book = Book(**infobox_data)
            session.add(new_book)
            session.commit()
            return jsonify(infobox_data), 200
        else:
            return jsonify({'error': 'Infobox not found'}), 404
    else:
        return jsonify({'error': 'Page ID not found'}), 404

@app.route('/visualize', methods=['GET'])
def visualize():
    books = session.query(Book).all()
    data = [{
        'title': book.title,
        'author': book.author,
        'publication_date': book.publication_date,
        'publication_place': book.publication_place
    } for book in books]
    return jsonify(data)

@app.route('/clear', methods=['POST'])
def clear_database():
    session.query(Book).delete()
    session.commit()
    return jsonify({'message': 'Database cleared'}), 200


if __name__ == '__main__':
    app.run(debug=True)
