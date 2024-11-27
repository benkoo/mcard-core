from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Base URL for the API
API_BASE_URL = "http://localhost:5000/api"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cards', methods=['GET'])
def get_cards():
    headers = {
        'x-api-key': 'YOUR_API_KEY'  # Replace with your actual API key
    }
    response = requests.get(f"{API_BASE_URL}/cards", headers=headers)
    if response.status_code == 200:
        try:
            return jsonify(response.json())
        except ValueError:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
    else:
        return jsonify({'error': 'Failed to retrieve cards', 'status_code': response.status_code}), response.status_code

@app.route('/card/<int:card_id>', methods=['GET'])
def get_card(card_id):
    response = requests.get(f"{API_BASE_URL}/card/{card_id}")
    return jsonify(response.json())

@app.route('/card', methods=['POST'])
def create_card():
    content = request.json['content']
    headers = {
        'x-api-key': 'YOUR_API_KEY'  # Replace with your actual API key
    }
    response = requests.post(f"{API_BASE_URL}/card", json={'content': content}, headers=headers)
    if response.status_code == 200:
        try:
            return jsonify(response.json())
        except ValueError:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
    else:
        print(f"Error response: {response.text}")  # Debugging line
        return jsonify({'error': 'Failed to create card', 'status_code': response.status_code}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
