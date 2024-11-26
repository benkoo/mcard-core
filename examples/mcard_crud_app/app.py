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
            content = card.content
            
            # Check for SVG content first
            if ContentTypeInterpreter.is_svg_content(content):
                content_type = 'image/svg+xml'
                is_image = True
                is_svg = True
                extension = 'svg'  # Add this line to set extension for SVG files
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

            current_page_cards.append({
                'content_hash': card.content_hash,
                'content': content,
                'content_type': content_type,
                'is_image': is_image,
                'is_svg': is_svg,
                'svg_content': content_str if is_svg else None,
                'time_claimed': card.time_claimed,
                'is_binary': is_binary,
                'name': f'Card {card.content_hash[:8]}'  # Generate a name if none exists
            })
        
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
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f'Error adding file content: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('new_card'))

@app.route('/view/<content_hash>')
def view_card(content_hash):
    """View a card's content."""
    storage = get_storage()
    card = storage.get(content_hash)
    
    if not card:
        flash('No card found', 'error')
        return redirect(url_for('index'))
    
    content = card.content
    is_binary = isinstance(content, bytes)
    
    # Get content size
    size = len(content) if content else 0
    
    # Check for SVG content first
    if ContentTypeInterpreter.is_svg_content(content):
        content_type = 'image/svg+xml'
        is_image = True
        is_svg = True
        extension = 'svg'  # Add this line to set extension for SVG files
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

@app.route('/binary/<content_hash>')
def get_binary_content(content_hash):
    """Serve binary content with proper content type."""
    storage = get_storage()
    card = storage.get(content_hash)
    
    if not card or not isinstance(card.content, bytes):
        return 'No binary content found', 404
    
    content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
    return Response(card.content, mimetype=content_type)

@app.route('/download/<content_hash>')
def download_card(content_hash):
    """Download a card's content."""
    storage = get_storage()
    card = storage.get(content_hash)
    
    if not card:
        flash('No card found', 'error')
        return redirect(url_for('index'))
    
    content = card.content
    is_binary = isinstance(content, bytes)
    
    if is_binary:
        content_type, extension = ContentTypeInterpreter.detect_content_type(content)
        filename = f"card_{content_hash[:8]}.{extension}"
        return send_file(
            BytesIO(content),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
    else:
        # For text content, create a text file
        content_str = str(content)
        filename = f"card_{content_hash[:8]}.txt"
        return send_file(
            BytesIO(content_str.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )

@app.route('/delete/<content_hash>', methods=['POST'])
def delete(content_hash):
    """Delete a card."""
    storage = get_storage()
    storage.delete(content_hash)
    flash('Card deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route('/thumbnail/<content_hash>')
def serve_thumbnail(content_hash):
    """Serve thumbnail for image content."""
    storage = get_storage()
    card = storage.get(content_hash)
    
    if not card or not isinstance(card.content, bytes):
        return 'No image content found', 404
    
    content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
    if not content_type.startswith('image/'):
        return 'Not an image', 400
    
    # For now, just serve the original image
    # TODO: Implement actual thumbnail generation
    return Response(card.content, mimetype=content_type)

if __name__ == '__main__':
    app.run(debug=True)
