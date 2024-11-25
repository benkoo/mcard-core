from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response
from urllib.parse import quote
from mcard.core import MCard
from mcard.storage import MCardStorage

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

def check_duplicate_content(storage, content):
    """Check if content already exists in storage."""
    try:
        # Get all cards and check for content match
        all_cards = storage.get_all()
        for card in all_cards:
            # Skip binary cards
            try:
                if isinstance(card.content, bytes):
                    if card.content == content:
                        return {"found": True, "hash": card.content_hash}
                    continue
                
                # For text content
                if card.content == content:
                    return {"found": True, "hash": card.content_hash}
                
            except Exception as e:
                print(f"Error comparing content: {e}")
                continue
                
        return {"found": False}
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return {"found": False}

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

@app.route('/api/cards', methods=['POST'])
def add_card():
    """Generic route to add any type of card to MCard storage."""
    try:
        print(f"Request method: {request.method}")  # Debug log
        print(f"Request files: {list(request.files.keys())}")  # Debug log
        print(f"Request form: {list(request.form.keys())}")  # Debug log
        
        storage = get_storage()
        
        # Check if this is a text form submission
        if 'content' in request.form:
            print("Handling text form submission")  # Debug log
            content = request.form.get('content')
            if not content:
                return jsonify({"error": "No content provided"}), 400
            
            # Check for duplicates
            duplicate_check = check_duplicate_content(storage, content)
            if duplicate_check["found"]:
                return jsonify({
                    "warning": "Same content was found, no new MCard created",
                    "hash": duplicate_check["hash"]
                }), 409
            
            # Store text content directly
            card = MCard(content=content)
            storage.save(card)
            storage.conn.commit()
            
            print(f"Stored text content with hash: {card.content_hash}")  # Debug log
            return redirect(url_for('view_card', content_hash=card.content_hash))
            
        # Check if this is a file upload
        if 'file' in request.files:
            file = request.files['file']
            print(f"\n=== File Upload Debug ===")
            print(f"File object: {file}")
            print(f"Original filename: {file.filename}")
            
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Get the file content
            content = file.read()
            content_type = file.content_type or 'application/octet-stream'
            
            print(f"Uploading file: {file.filename}")
            print(f"Content type: {content_type}")
            print(f"Content size: {len(content)} bytes")
            
            # Check for duplicates
            duplicate_check = check_duplicate_content(storage, content)
            if duplicate_check["found"]:
                return jsonify({
                    "warning": "Same content was found, no new MCard created",
                    "hash": duplicate_check["hash"]
                }), 409
            
            # Store binary content directly
            card = MCard(content=content)
            storage.save(card)
            storage.conn.commit()
            
            print(f"Stored binary content with hash: {card.content_hash}")
            return redirect(url_for('view_card', content_hash=card.content_hash))
            
        # Handle JSON data
        content_type = request.headers.get('Content-Type', 'application/json')
        if content_type == 'application/json':
            if not request.is_json:
                return jsonify({"error": "Expected JSON data"}), 400
            content = request.get_json()
            if not content:
                return jsonify({"error": "No content provided"}), 400
            content_str = json.dumps(content)
        
        elif content_type == 'text/plain':
            # Handle UTF-8 text data
            content = request.get_data(as_text=True)
            if not content:
                return jsonify({"error": "No content provided"}), 400
            content_str = content
            
        else:
            # Handle raw binary data (non-file upload)
            content = request.get_data()
            if not content:
                return jsonify({"error": "No content provided"}), 400
            
            # Store binary data directly
            card = MCard(content=content)
            storage.save(card)
            storage.conn.commit()
            return redirect(url_for('view_card', content_hash=card.content_hash))

        # Store text/JSON content
        storage = get_storage()
        card = MCard(content=content_str)
        storage.save(card)
        storage.conn.commit()
        return redirect(url_for('view_card', content_hash=card.content_hash))

    except Exception as e:
        print(f"Error in add_card: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/new_card')
def new_card():
    """Route to display the new card creation page."""
    return render_template('new_card.html')

@app.route('/view/<content_hash>')
def view_card(content_hash):
    try:
        storage = get_storage()
        card = storage.get(content_hash)
        if not card:
            return "Card not found", 404
            
        is_binary = isinstance(card.content, bytes)
        content_type = None
        
        if is_binary:
            # Detect image type
            if card.content.startswith(b'\x89PNG'):
                content_type = 'image/png'
            elif card.content.startswith(b'\xff\xd8\xff'):
                content_type = 'image/jpeg'
            elif card.content.startswith(b'GIF87a') or card.content.startswith(b'GIF89a'):
                content_type = 'image/gif'
            elif card.content.startswith(b'RIFF') and card.content[8:12] == b'WEBP':
                content_type = 'image/webp'
        
        return render_template('view_card.html', 
                             content_hash=content_hash,
                             card=card,
                             content=None if is_binary else str(card.content),
                             is_binary=is_binary,
                             is_image=content_type is not None,
                             size=len(card.content) if card.content else 0)
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
        content_type = 'application/octet-stream'
        filename = None

        if isinstance(content, bytes):
            # Try to detect content type from the first few bytes
            if content.startswith(b'\x89PNG\r\n\x1a\n'):
                content_type = 'image/png'
                filename = 'image.png'
            elif content.startswith(b'\xff\xd8\xff'):
                content_type = 'image/jpeg'
                filename = 'image.jpg'
            elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
                content_type = 'image/gif'
                filename = 'image.gif'
            elif content.startswith(b'RIFF') and content[8:12] == b'WEBP':
                content_type = 'image/webp'
                filename = 'image.webp'

        # Handle download flag
        if request.args.get('download') == 'true':
            headers = {
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{filename or "file"}"'
            }
        else:
            headers = {'Content-Type': content_type}

        print(f"Serving content with type: {content_type}, size: {len(content)} bytes")
        return Response(content, headers=headers)

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

        is_binary = isinstance(card.content, bytes)
        
        # Set default content type and extension
        content_type = 'text/plain'
        extension = 'txt'
        
        if is_binary:
            # Check for image types
            if card.content.startswith(b'\x89PNG'):
                content_type = 'image/png'
                extension = 'png'
            elif card.content.startswith(b'\xff\xd8\xff'):
                content_type = 'image/jpeg'
                extension = 'jpg'
            elif card.content.startswith(b'GIF87a') or card.content.startswith(b'GIF89a'):
                content_type = 'image/gif'
                extension = 'gif'
            elif card.content.startswith(b'RIFF') and card.content[8:12] == b'WEBP':
                content_type = 'image/webp'
                extension = 'webp'
            else:
                content_type = 'application/octet-stream'
                extension = 'bin'
        else:
            # Check for JSON content
            try:
                json.loads(card.content)
                content_type = 'application/json'
                extension = 'json'
            except (json.JSONDecodeError, TypeError):
                pass  # Keep default text/plain
        
        filename = f"{content_hash[:8]}.{extension}"
        quoted_filename = quote(filename)
        
        response = Response(card.content)
        response.headers.set('Content-Type', content_type)
        response.headers.set('Content-Disposition', f'attachment; filename="{quoted_filename}"')
        return response

    except Exception as e:
        print(f"Error in download_card: {str(e)}")
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
