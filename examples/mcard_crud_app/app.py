from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response, flash
from mcard import MCard, MCardStorage, ContentTypeInterpreter
from urllib.parse import quote

app = Flask(__name__)

# Add min and max functions to Jinja2 environment
app.jinja_env.globals.update(min=min, max=max)

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
    """Display all cards."""
    cards = []
    print("\n=== Getting all cards ===")  # Debug log
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        storage = get_storage()
        all_cards = storage.get_all()
        print(f"Found {len(all_cards)} cards")  # Debug log
        
        # Calculate total pages
        total_cards = len(all_cards)
        total_pages = (total_cards + per_page - 1) // per_page
        
        # Ensure page is within bounds
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        # Calculate slice indices for current page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_cards)
        
        # Get cards for current page
        current_cards = all_cards[start_idx:end_idx]
        
        # Process each card
        for card in current_cards:
            try:
                # First try to decode as UTF-8 to check if it's text
                try:
                    content_str = card.content.decode('utf-8') if isinstance(card.content, bytes) else card.content
                except UnicodeDecodeError:
                    print(f"Binary card: {card.content_hash}")
                    cards.append({
                        'id': card.content_hash,
                        'type': 'binary',
                        'size': len(card.content),
                        'time_claimed': card.time_claimed
                    })
                    continue

                # Try to parse as JSON
                try:
                    content = json.loads(content_str)
                    cards.append({
                        'id': card.content_hash,
                        'type': 'json',
                        'content': json.dumps(content, indent=2),
                        'time_claimed': card.time_claimed
                    })
                except json.JSONDecodeError:
                    # Plain text
                    cards.append({
                        'id': card.content_hash,
                        'type': 'text',
                        'content': content_str,
                        'time_claimed': card.time_claimed
                    })
                    
            except Exception as e:
                print(f"Error processing card {card.content_hash}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error in index: {str(e)}")  # Debug log
        raise
        
    # Pagination info
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_cards': total_cards,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }
    
    return render_template('index.html', cards=cards, pagination=pagination)

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

if __name__ == '__main__':
    app.run(debug=True)
