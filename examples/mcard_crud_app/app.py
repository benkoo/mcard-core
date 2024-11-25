from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response, flash, send_file
from mcard import MCard, MCardStorage, ContentTypeInterpreter
from urllib.parse import quote
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'dev'  # For development only. Use a secure key in production.

# Add min and max functions to Jinja2 environment
app.jinja_env.globals.update(min=min, max=max)

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(value):
    """Format a datetime object."""
    if value is None:
        return ""
    return value.strftime('%Y-%m-%d %H:%M:%S')

# Initialize database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcard_crud.db")
print(f"Using database at: {db_path}")  # Debug log

# Ensure the database directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

def get_storage():
    """Get thread-local storage instance."""
    if 'storage' not in g:
        g.storage = MCardStorage(db_path)
    return g.storage

@app.teardown_appcontext
def teardown_db(exception):
    """Close database connection when app context ends."""
    storage = g.pop('storage', None)
    if storage is not None:
        storage.conn.close()

@app.route('/')
def index():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get all cards using storage
        storage = get_storage()
        all_cards = list(storage.get_all())
        
        # Calculate pagination values
        total_items = len(all_cards)
        total_pages = max((total_items + per_page - 1) // per_page, 1)
        
        # Ensure page is within valid range
        page = min(max(page, 1), total_pages)
        
        # Slice the cards for current page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_items)
        page_cards = all_cards[start_idx:end_idx]

        # Convert MCard objects to dictionaries with required attributes
        current_page_cards = []
        for card in page_cards:
            # Determine content type
            content_type = "text/plain"
            is_binary = isinstance(card.content, bytes)
            if is_binary:
                content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
            
            card_dict = {
                'hash': card.content_hash,
                'content': card.content,
                'time_claimed': card.time_claimed,
                'content_type': content_type,
                'is_image': ContentTypeInterpreter.is_image_content(content_type),
                'is_binary': is_binary
            }
            current_page_cards.append(card_dict)
        
        return render_template('index.html',
                             cards=current_page_cards,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             total_items=total_items)
    except Exception as e:
        app.logger.error(f"Error in index: {str(e)}")
        # Redirect to new card page if there's an error
        return redirect(url_for('new_card'))

@app.route('/grid')
def grid_view():
    try:
        # Get grid parameters
        page = request.args.get('page', 1, type=int)
        rows = request.args.get('rows', 3, type=int)
        cols = request.args.get('cols', 3, type=int)
        
        # Calculate items per page based on grid size
        per_page = rows * cols
        
        # Get all cards using storage
        storage = get_storage()
        all_cards = list(storage.get_all())
        
        # Calculate pagination values
        total_items = len(all_cards)
        total_pages = max((total_items + per_page - 1) // per_page, 1)
        
        # Ensure page is within valid range
        page = min(max(page, 1), total_pages)
        
        # Slice the cards for current page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_items)
        page_cards = all_cards[start_idx:end_idx]

        # Convert MCard objects to dictionaries with required attributes
        current_page_cards = []
        for card in page_cards:
            # Determine content type
            content_type = "text/plain"
            is_binary = isinstance(card.content, bytes)
            if is_binary:
                content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
            
            card_dict = {
                'hash': card.content_hash,
                'content': card.content,
                'time_claimed': card.time_claimed,
                'content_type': content_type,
                'is_image': ContentTypeInterpreter.is_image_content(content_type),
                'is_binary': is_binary
            }
            current_page_cards.append(card_dict)
        
        return render_template('grid.html',
                             cards=current_page_cards,
                             page=page,
                             rows=rows,
                             cols=cols,
                             total_pages=total_pages,
                             total_items=total_items)
    except Exception as e:
        app.logger.error(f"Error in grid_view: {str(e)}")
        return redirect(url_for('new_card'))

@app.route('/new')
def new_card():
    """Display form for creating a new card."""
    warning = request.args.get('warning')
    hash = request.args.get('hash')
    return render_template('new_card.html', warning=warning, hash=hash)

@app.route('/add_text_card', methods=['POST'])
def add_text_card():
    """Add a new text card."""
    app.logger.info('=== Starting add_text_card ===')
    storage = get_storage()
    content = request.form.get('content')
    app.logger.info(f'Received content (first 100 chars): {content[:100] if content else None}')
    
    if not content:
        app.logger.warning('No content provided')
        flash('No content provided', 'error')
        return redirect(url_for('new_card'))

    try:
        app.logger.info('Checking for duplicate text content')
        
        # Check for duplicate content
        app.logger.info('About to call ContentTypeInterpreter.check_duplicate_content')
        duplicate_check = ContentTypeInterpreter.check_duplicate_content(storage, content)
        app.logger.info(f'Duplicate check result: {duplicate_check}')
        
        if duplicate_check["found"]:
            app.logger.info(f'Found existing card with hash {duplicate_check["hash"]}')
            return redirect(url_for('new_card', 
                warning="This content already exists",
                hash=duplicate_check["hash"]))

        # Create and save the new card
        app.logger.info('Creating new MCard')
        card = MCard(content=content)
        app.logger.info(f'Generated hash for new card: {card.content_hash}')
        storage.save(card)
        app.logger.info(f'Successfully added text content with hash {card.content_hash}')
        return redirect(url_for('view_card', content_hash=card.content_hash))
    except Exception as e:
        app.logger.error(f'Error adding text content: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('new_card'))

@app.route('/add_file_card', methods=['POST'])
def add_file_card():
    """Add a new file card."""
    storage = get_storage()
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('new_card'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('new_card'))

    try:
        # Read file content as bytes
        content = file.read()
        app.logger.info('Checking for duplicate file content')
        
        # Check for duplicate content
        duplicate_check = ContentTypeInterpreter.check_duplicate_content(storage, content)
        if duplicate_check["found"]:
            app.logger.info(f'Found existing card with hash {duplicate_check["hash"]}')
            return redirect(url_for('new_card',
                warning="This content already exists",
                hash=duplicate_check["hash"]))

        # Create and save the new card
        card = MCard(content=content)
        storage.save(card)
        app.logger.info(f'Successfully added file content with hash {card.content_hash}')
        return redirect(url_for('view_card', content_hash=card.content_hash))
    except Exception as e:
        app.logger.error(f'Error adding file content: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('new_card'))

@app.route('/delete/<content_hash>', methods=['POST'])
def delete(content_hash):
    """Delete a card."""
    try:
        storage = get_storage()
        storage.delete(content_hash)
        storage.conn.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/view/<content_hash>')
def view_card(content_hash):
    try:
        storage = get_storage()
        card = storage.get(content_hash)
        if not card:
            return "Card not found", 404
            
        content = card.content
        size = len(content)
        
        # Try to decode content if it's text
        is_binary = isinstance(content, bytes)
        if is_binary:
            mime_type, extension = ContentTypeInterpreter.detect_content_type(content)
            content_str = None
            is_image = mime_type.startswith('image/')
        else:
            content_str = str(content)
            mime_type = 'text/plain'
            extension = 'txt'
            is_image = False
        
        return render_template('view_card.html', 
                             content_hash=content_hash,
                             card=card,
                             content=content_str,
                             is_binary=is_binary,
                             is_image=is_image,
                             content_type=mime_type,
                             extension=extension,
                             size=size)
    except Exception as e:
        print(f"Error in view_card: {str(e)}")
        return f"Error viewing card: {str(e)}", 500

@app.route('/get_binary_content/<content_hash>')
def get_binary_content(content_hash):
    """Serve binary content with proper content type."""
    try:
        storage = get_storage()
        print(f"\n=== Get Binary Content Debug ===")
        print(f"Retrieving binary content for hash: {content_hash}")
        
        card = storage.get(content_hash)
        if not card:
            print(f"Content not found for hash: {content_hash}")
            return "Content not found", 404

        content = card.content
        download_info = ContentTypeInterpreter.prepare_download_response(content, content_hash)
        print(f"Serving content with type: {download_info['mime_type']}, size: {len(content)} bytes")
        return Response(content, headers=download_info['headers'])

    except Exception as e:
        print(f"Error serving binary content: {str(e)}")
        return f"Error serving binary content: {str(e)}", 500

@app.route('/download/<content_hash>')
def download_card(content_hash):
    try:
        storage = get_storage()
        card = storage.get(content_hash)
        if not card:
            return "Card not found", 404

        content = card.content
        download_info = ContentTypeInterpreter.prepare_download_response(content, content_hash)
        response = Response(content)
        for key, value in download_info['headers'].items():
            response.headers.set(key, value)
        return response

    except Exception as e:
        print(f"Error in download_card: {str(e)}")
        return str(e), 500

@app.route('/content/<content_hash>/thumbnail')
def serve_thumbnail(content_hash):
    """Serve thumbnail for image content."""
    try:
        storage = get_storage()
        card = storage.get(content_hash)
        if not card:
            return "Content not found", 404

        # Detect content type
        content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
        
        # Only serve if it's an image
        if ContentTypeInterpreter.is_image_content(content_type):
            return send_file(
                BytesIO(card.content),
                mimetype=content_type
            )
        
        return "Not an image", 400
    except Exception as e:
        app.logger.error(f'Error serving thumbnail: {str(e)}')
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
