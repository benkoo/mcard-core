from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
import logging
from dotenv import load_dotenv
from jinja2 import Environment

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')  # Required for flash messages
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# API configuration
API_BASE_URL = "http://localhost:8000"
MCARD_API_KEY = os.getenv('MCARD_API_KEY', 'test_api_key')
MCARD_API_URL = API_BASE_URL
HEADERS = {'x-api-key': MCARD_API_KEY}

app.jinja_env.filters['min'] = lambda value, other: min(value, other)
app.jinja_env.filters['max'] = lambda value, other: max(value, other)

def format_binary_content(content):
    """Format binary content for display with different representations."""
    if isinstance(content, str):
        content = content.encode('latin1')
    
    result = {
        'hex': content.hex(),
        'length': len(content),
        'preview': None,
        'type_hint': 'unknown'
    }
    
    # Try to detect content type
    if content.startswith(b'\x89PNG\r\n'):
        result['type_hint'] = 'PNG image'
    elif content.startswith(b'\xff\xd8\xff'):
        result['type_hint'] = 'JPEG image'
    elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
        result['type_hint'] = 'GIF image'
    elif content.startswith(b'%PDF'):
        result['type_hint'] = 'PDF document'
    
    # Try to get a text preview if it might be text
    try:
        preview = content.decode('utf-8')[:100]
        if len(preview) == 100:
            preview += '...'
        result['preview'] = preview
        if result['type_hint'] == 'unknown':
            result['type_hint'] = 'text (UTF-8)'
    except UnicodeDecodeError:
        pass
    
    return result

def format_card_content(card):
    """Format card content based on its type and structure."""
    if not card or 'content' not in card:
        return card
    
    content = card['content']
    
    # If content is a string and looks like base64-encoded data
    if isinstance(content, str) and content.startswith(('data:', 'iVBOR', '/9j/', 'JVBERi')):
        card['content_type'] = 'binary'
        card['is_image'] = content.startswith(('iVBOR', '/9j/'))  # PNG or JPEG
        card['is_pdf'] = content.startswith('JVBERi')  # PDF
        return card
    
    # If content is a string and looks like text (all printable ASCII)
    if isinstance(content, str) and all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in content):
        card['content_type'] = 'text'
        card['is_text'] = True
        return card
    
    # Handle binary content
    try:
        # If it's bytes, convert to base64
        if isinstance(content, bytes):
            import base64
            content_b64 = base64.b64encode(content).decode('utf-8')
            card['content'] = content_b64
            card['content_type'] = 'binary'
        # If it's a string that might be binary data
        elif isinstance(content, str):
            # Try to encode as base64 if it looks like binary
            try:
                binary_data = content.encode('latin1')
                import base64
                content_b64 = base64.b64encode(binary_data).decode('utf-8')
                card['content'] = content_b64
                card['content_type'] = 'binary'
            except Exception:
                # If encoding fails, treat as text
                card['content_type'] = 'text'
                card['is_text'] = True
        else:
            # For other types, convert to string
            card['content'] = str(content)
            card['content_type'] = 'text'
            card['is_text'] = True
        
        # Try to detect content type if binary
        if card['content_type'] == 'binary':
            # Convert base64 back to bytes for detection
            try:
                import base64
                binary_data = base64.b64decode(card['content'])
                
                # Detect file type
                card['is_image'] = binary_data.startswith((b'\x89PNG\r\n', b'\xff\xd8\xff'))  # PNG or JPEG
                card['is_pdf'] = binary_data.startswith(b'%PDF')  # PDF
                
                # Try to decode as text
                try:
                    text_content = binary_data.decode('utf-8')
                    # Check if it's mostly printable text
                    if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in text_content):
                        card['is_text'] = True
                        card['content'] = text_content  # Replace base64 content with decoded text
                        card['content_type'] = 'text'
                        return card
                except UnicodeDecodeError:
                    try:
                        # Try latin1 as fallback
                        text_content = binary_data.decode('latin1')
                        if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in text_content):
                            card['is_text'] = True
                            card['content'] = text_content  # Replace base64 content with decoded text
                            card['content_type'] = 'text'
                            return card
                    except Exception:
                        # If both decodings fail, keep as binary and show hex preview
                        card['hex_preview'] = ' '.join(f'{b:02x}' for b in binary_data[:50])
                        if len(binary_data) > 50:
                            card['hex_preview'] += ' ...'
            except Exception as e:
                app.logger.error(f"Error processing binary content: {str(e)}")
    except Exception as e:
        app.logger.error(f"Error formatting card content: {str(e)}")
        card['content_type'] = 'binary'
        card['error'] = str(e)
    
    return card

@app.route('/')
def index():
    """Home page shows the card catalog with pagination."""
    try:
        # Get pagination and grid parameters from request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        grid_rows = request.args.get('grid_rows', 3, type=int)
        grid_cols = request.args.get('grid_cols', 3, type=int)
        
        # Validate and cap parameters
        per_page = min(max(per_page, 10), 50)  # Between 10 and 50
        grid_rows = min(max(grid_rows, 2), 5)  # Between 2 and 5
        grid_cols = min(max(grid_cols, 2), 5)  # Between 2 and 5
        
        # Fetch all cards
        headers = {'x-api-key': MCARD_API_KEY}
        response = requests.get(f"{API_BASE_URL}/cards/", headers=headers)
        response.raise_for_status()
        all_cards = response.json()
        
        # Calculate pagination
        total_cards = len(all_cards)
        total_pages = (total_cards + per_page - 1) // per_page
        page = min(max(page, 1), total_pages) if total_pages > 0 else 1
        
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_cards)
        cards = all_cards[start_idx:end_idx]
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_cards': total_cards,
            'has_prev': page > 1,
            'has_next': page < total_pages,
        }
        
        return render_template('card_catalog_page.html',
                             cards=cards,
                             pagination=pagination,
                             grid_rows=grid_rows,
                             grid_cols=grid_cols)
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching cards: {str(e)}', 'error')
        return render_template('card_catalog_page.html',
                             cards=[],
                             pagination={'page': 1, 'total_pages': 1, 'per_page': 10},
                             grid_rows=3,
                             grid_cols=3)

@app.route('/catalog')
def card_catalog():
    """Display all cards in a catalog view."""
    try:
        # Get pagination parameters from request
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        grid_rows = request.args.get('grid_rows', 3, type=int)
        grid_cols = request.args.get('grid_cols', 3, type=int)
        
        # Validate and cap parameters
        per_page = min(max(per_page, 10), 50)  # Between 10 and 50
        grid_rows = min(max(grid_rows, 2), 5)  # Between 2 and 5
        grid_cols = min(max(grid_cols, 2), 5)  # Between 2 and 5
        
        # Fetch all cards
        headers = {'x-api-key': MCARD_API_KEY}
        response = requests.get(f"{API_BASE_URL}/cards/", headers=headers)
        response.raise_for_status()
        all_cards = response.json()
        
        # Calculate pagination
        total_cards = len(all_cards)
        total_pages = (total_cards + per_page - 1) // per_page
        page = min(max(page, 1), total_pages) if total_pages > 0 else 1
        
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_cards)
        cards = all_cards[start_idx:end_idx]
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'total_cards': total_cards,
            'has_prev': page > 1,
            'has_next': page < total_pages,
        }
        
        return render_template('card_catalog_page.html',
                             cards=cards,
                             pagination=pagination,
                             grid_rows=grid_rows,
                             grid_cols=grid_cols)
    except requests.exceptions.RequestException as e:
        flash(f'Error fetching cards: {str(e)}', 'error')
        return render_template('card_catalog_page.html',
                             cards=[],
                             pagination={'page': 1, 'total_pages': 1, 'per_page': 10},
                             grid_rows=3,
                             grid_cols=3)

@app.route('/card/<string:card_hash>')
def card_detail(card_hash):
    """View details of a specific card."""
    try:
        app.logger.info(f"Fetching card details for hash: {card_hash}")
        response = requests.get(f'{MCARD_API_URL}/cards/{card_hash}', headers=HEADERS)
        app.logger.info(f"Card detail response status: {response.status_code}")
        
        if response.status_code == 200:
            card = response.json()
            card = format_card_content(card)
            app.logger.info(f"Rendering card details with content type: {card.get('content_type', 'unknown')}")
            return render_template('single_card_page.html', card=card)
        else:
            app.logger.error(f"Failed to fetch card. Status: {response.status_code}, Response: {response.text}")
            flash('Card not found', 'error')
            return redirect(url_for('card_catalog'))
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error retrieving card: {str(e)}")
        flash(f'Error retrieving card: {str(e)}', 'error')
        return redirect(url_for('card_catalog'))

@app.route('/cards/<string:card_hash>', methods=['DELETE'])
def delete_card(card_hash):
    """Delete a specific card."""
    api_url = f"{MCARD_API_URL}/cards/{card_hash}"
    app.logger.info(f"Attempting to delete card at: {api_url}")
    
    try:
        response = requests.delete(api_url, headers=HEADERS)
        app.logger.info(f"Delete response status: {response.status_code}")
        app.logger.info(f"Delete response headers: {response.headers}")
        
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Card deleted successfully'})
        else:
            app.logger.error(f"Failed to delete card. Status: {response.status_code}")
            app.logger.error(f"Response content: {response.text}")
            return jsonify({'status': 'error', 'message': 'Failed to delete card'}), response.status_code
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error deleting card: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/new_card', methods=['GET', 'POST'])
def new_card():
    """Handle new card creation."""
    if request.method == 'POST':
        content_type = request.form.get('content_type', 'text')
        
        if content_type == 'text':
            content = request.form.get('content')
            if not content:
                flash('Content is required', 'error')
                return redirect(url_for('new_card'))
        else:  # Binary upload
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('new_card'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('new_card'))
            
            try:
                # Read binary content and convert to base64
                import base64
                binary_content = file.read()
                
                # Try to detect if it's text content
                try:
                    # Try UTF-8 first
                    text_content = binary_content.decode('utf-8')
                    # Check if it's mostly printable text
                    if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in text_content):
                        # If it's text, send it as text content
                        content = text_content
                        content_type = 'text'
                    else:
                        # If not, encode as base64
                        content = base64.b64encode(binary_content).decode('utf-8')
                        content_type = 'binary'
                except UnicodeDecodeError:
                    try:
                        # Try latin1 as fallback
                        text_content = binary_content.decode('latin1')
                        if all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in text_content):
                            content = text_content
                            content_type = 'text'
                        else:
                            content = base64.b64encode(binary_content).decode('utf-8')
                            content_type = 'binary'
                    except Exception:
                        content = base64.b64encode(binary_content).decode('utf-8')
                        content_type = 'binary'
            except Exception as e:
                flash(f'Error reading file: {str(e)}', 'error')
                return redirect(url_for('new_card'))
        
        headers = {'x-api-key': MCARD_API_KEY}
        try:
            response = requests.post(
                f"{API_BASE_URL}/cards/",
                json={'content': content},
                headers=headers
            )
            response.raise_for_status()
            flash('Card created successfully', 'success')
            return redirect(url_for('card_catalog'))
        except requests.exceptions.RequestException as e:
            flash(f'Error creating card: {str(e)}', 'error')
            return redirect(url_for('new_card'))
    
    return render_template('new_card_page.html')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    flash('The requested page was not found', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    flash('An internal server error occurred', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
