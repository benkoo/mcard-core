from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response, flash, send_file
from mcard import MCard, SQLiteRepository as MCardStorage, ContentTypeInterpreter, DatabaseSettings
from urllib.parse import quote
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'dev'  # For development only. Use a secure key in production.

# Add min and max functions to Jinja2 environment
def format_time(time_value):
    if time_value is None:
        return 'N/A'
    if isinstance(time_value, str):
        try:
            time_value = datetime.fromisoformat(time_value)
        except ValueError:
            return 'N/A'
    if isinstance(time_value, datetime):
        return time_value.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'

app.jinja_env.globals.update(min=min, max=max, format_time=format_time)

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(value):
    """Format a datetime object."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
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
    if storage is not None and hasattr(storage, '_local'):
        if hasattr(storage._local, 'connection'):
            storage._local.connection.close()

@app.route('/')
def index():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get all cards using storage
        storage = get_storage()
        all_cards = []
        with storage.connection as conn:
            cursor = conn.execute("SELECT * FROM card ORDER BY g_time DESC")
            for row in cursor:
                all_cards.append({
                    'hash': row['hash'],
                    'content': row['content'],
                    'g_time': row['g_time']
                })
        
        # Calculate pagination values
        total_items = len(all_cards)
        total_pages = max((total_items + per_page - 1) // per_page, 1)
        
        # Ensure page is within valid range
        page = min(max(page, 1), total_pages)
        
        # Slice the cards for current page
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_items)
        page_cards = all_cards[start_idx:end_idx]

        # Convert cards to dictionaries with required attributes
        current_page_cards = []
        for card in page_cards:
            content = card['content']
            
            # Check for SVG content first
            if ContentTypeInterpreter.is_svg_content(content):
                content_type = 'image/svg+xml'
                is_image = True
                is_svg = True
                extension = 'svg'
                # Ensure content is string for SVG
                content_str = content if isinstance(content, str) else content.decode('utf-8')
                content = content_str
            else:
                # Determine content type for non-SVG content
                is_binary = isinstance(content, bytes)
                is_svg = False
                if is_binary:
                    content_type, _ = ContentTypeInterpreter.detect_content_type(content)
                    content_str = None
                    is_image = content_type.startswith('image/')
                else:
                    content_str = str(content)
                    content_type = 'text/plain'
                    is_image = False
                    content = content_str

            card.update({
                'content': content,
                'content_type': content_type,
                'is_image': is_image,
                'is_svg': is_svg,
                'svg_content': content_str if is_svg else None,
                'is_binary': is_binary,
                'name': f'Card {card["hash"][:8]}'  # Generate a name if none exists
            })
            current_page_cards.append(card)
        
        return render_template('index.html',
                             cards=current_page_cards,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             total_items=total_items)
    except Exception as e:
        app.logger.error(f"Error in index: {str(e)}")
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('index.html',
                             cards=[],
                             page=1,
                             per_page=10,
                             total_pages=1,
                             total_items=0)

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
        
        # Create temporary MCard to generate hash
        temp_card = MCard(content=content)
        card = {
            'hash': temp_card.hash,
            'content': content,
            'g_time': temp_card.g_time
        }
        
        # Check for duplicate content
        app.logger.info('About to check for duplicate content')
        with storage.connection as conn:
            cursor = conn.execute("SELECT hash FROM card WHERE hash = ?", (card['hash'],))
            if cursor.fetchone():
                app.logger.info(f'Found existing card with hash {card["hash"]}')
                return redirect(url_for('new_card', 
                    warning="This content already exists",
                    hash=card['hash']))

            # Save the new card
            app.logger.info('Saving new MCard')
            conn.execute(
                "INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                (card['hash'], card['content'], card['g_time'])
            )
            
        app.logger.info(f'Successfully added text content with hash {card["hash"]}')
        return redirect(url_for('index'))
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
        
        # Create temporary MCard to generate hash
        temp_card = MCard(content=content)
        card = {
            'hash': temp_card.hash,
            'content': content,
            'g_time': temp_card.g_time
        }
        
        # Check for duplicate content
        with storage.connection as conn:
            cursor = conn.execute("SELECT hash FROM card WHERE hash = ?", (card['hash'],))
            if cursor.fetchone():
                app.logger.info(f'Found existing card with hash {card["hash"]}')
                return redirect(url_for('new_card',
                    warning="This content already exists",
                    hash=card['hash']))

            # Save the new card
            conn.execute(
                "INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                (card['hash'], card['content'], card['g_time'])
            )
            
        app.logger.info(f'Successfully added file content with hash {card["hash"]}')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f'Error adding file content: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('new_card'))

@app.route('/view/<content_hash>')
def view_card(content_hash):
    """View a card's content."""
    storage = get_storage()
    
    with storage.connection as conn:
        cursor = conn.execute("SELECT * FROM card WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        
        if not row:
            flash('No card found', 'error')
            return redirect(url_for('index'))
        
        # Convert row to dict for template
        card = {
            'hash': row['hash'],
            'content': row['content'],
            'g_time': row['g_time']
        }
    
    content = card['content']
    is_binary = isinstance(content, bytes)
    
    # Get content size
    size = len(content) if content else 0
    
    # Check for SVG content first
    if ContentTypeInterpreter.is_svg_content(content):
        content_type = 'image/svg+xml'
        is_image = True
        is_svg = True
        extension = 'svg'
        # Ensure content is string for SVG
        content = content if isinstance(content, str) else content.decode('utf-8')
    else:
        # Determine content type for non-SVG content
        is_svg = False
        if is_binary:
            content_type, extension = ContentTypeInterpreter.detect_content_type(content)
            is_image = content_type.startswith('image/')
            content = None  # Don't pass binary content to template
        else:
            content = str(content)
            content_type = 'text/plain'
            extension = 'txt'
            is_image = False
    
    return render_template('view_card.html',
                         card=card,
                         content=content,
                         content_type=content_type,
                         extension=extension,
                         size=size,
                         is_binary=is_binary,
                         is_image=is_image,
                         is_svg=is_svg)

@app.route('/delete/<content_hash>', methods=['POST'])
def delete(content_hash):
    """Delete a card."""
    storage = get_storage()
    with storage.connection as conn:
        conn.execute("DELETE FROM card WHERE hash = ?", (content_hash,))
    flash('Card deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route('/binary/<content_hash>')
def get_binary_content(content_hash):
    """Serve binary content with proper content type."""
    storage = get_storage()
    with storage.connection as conn:
        cursor = conn.execute("SELECT content FROM card WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        if not row:
            return 'Content not found', 404
        content = row['content']
    
    content_type, _ = ContentTypeInterpreter.detect_content_type(content)
    return Response(content, mimetype=content_type)

@app.route('/download/<content_hash>')
def download_card(content_hash):
    """Download card content."""
    storage = get_storage()
    with storage.connection as conn:
        cursor = conn.execute("SELECT * FROM card WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        if not row:
            flash('Card not found', 'error')
            return redirect(url_for('index'))
            
        content = row['content']
        time_claimed = datetime.fromisoformat(row['g_time'])
        card = MCard(content=content, hash=row['hash'], g_time=row['g_time'])
    
    content = card.content
    is_binary = isinstance(content, bytes)
    
    if is_binary:
        content_type, extension = ContentTypeInterpreter.detect_content_type(content)
    else:
        content = str(content).encode('utf-8')
        content_type = 'text/plain'
        extension = 'txt'
    
    filename = f"card_{card.hash[:8]}.{extension}"
    
    return send_file(
        BytesIO(content),
        mimetype=content_type,
        as_attachment=True,
        download_name=filename
    )

@app.route('/thumbnail/<content_hash>')
def serve_thumbnail(content_hash):
    """Serve thumbnail for image content."""
    storage = get_storage()
    with storage.connection as conn:
        cursor = conn.execute("SELECT content FROM card WHERE hash = ?", (content_hash,))
        row = cursor.fetchone()
        if not row:
            return 'Content not found', 404
        content = row['content']
    
    if not isinstance(content, bytes):
        return 'Not a binary content', 400
        
    content_type, _ = ContentTypeInterpreter.detect_content_type(content)
    if not content_type.startswith('image/'):
        return 'Not an image', 400
        
    return Response(content, mimetype=content_type)

if __name__ == '__main__':
    app.run(debug=True)
