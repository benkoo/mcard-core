from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response, flash, send_file, session, make_response
from flask_cors import CORS
import asyncio
import mimetypes
from mcard.domain.models.card import MCard
from mcard.infrastructure.setup import MCardSetup
from mcard.domain.dependency.interpreter import ContentTypeInterpreter
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, TextAreaField
from wtforms.validators import DataRequired
from urllib.parse import quote
from io import BytesIO
import functools
import logging
from logging.handlers import RotatingFileHandler
import base64
from markupsafe import Markup
import uuid

# Import configuration and forms
from config import *
from forms import TextCardForm, FileCardForm, DeleteCardForm, NewCardForm
from utils import RequestParamHandler

# Configure Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['WTF_CSRF_SECRET_KEY'] = CSRF_SECRET_KEY
app.config['WTF_CSRF_ENABLED'] = True
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_SIZE

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Don't log binary data and sensitive info
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('flask').setLevel(logging.WARNING)

# Initialize CSRF protection
csrf = CSRFProtect(app)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors by redirecting to the form page."""
    logger.error(f"CSRF error: {str(e)}")
    flash("Invalid form submission. Please try again.", "error")
    return redirect(url_for('index'))

# Initialize CORS with CSRF support
CORS(app, supports_credentials=True)

# Initialize MCardSetup
mcard_setup = None

# Global storage variable
storage = None

async def init_mcard():
    """Initialize MCard storage system."""
    global storage, mcard_setup
    try:
        if mcard_setup is None:
            logger.info(f"Initializing MCard with database at: {DB_PATH}")
            mcard_setup = MCardSetup(
                db_path=DB_PATH,
                max_connections=DB_MAX_CONNECTIONS,
                timeout=DB_TIMEOUT,
                max_content_size=MAX_CONTENT_SIZE
            )
            await mcard_setup.initialize()
        
        # Ensure storage is created
        if storage is None:
            storage = mcard_setup.storage
            logger.info("MCard storage initialized")
        
        return storage
    except Exception as e:
        logger.error(f"Failed to initialize MCard: {e}", exc_info=True)
        raise

async def get_storage():
    """Get storage instance."""
    global storage
    try:
        if storage is None:
            await init_mcard()
        return storage
    except Exception as e:
        logger.error(f"Failed to get storage: {e}", exc_info=True)
        raise

@app.teardown_appcontext
async def teardown_storage(exception):
    """Close the storage connection at the end of each request."""
    global storage
    if storage is not None:
        try:
            await storage.close()
        except Exception as e:
            logger.error(f"Error closing storage: {e}", exc_info=True)
        storage = None

# Async wrapper for route handlers
def async_route(f):
    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in async route {f.__name__}: {e}", exc_info=True)
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for('index'))
    return wrapper

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
    """Format a datetime object or timestamp string."""
    if value is None:
        return ""
    
    # If it's already a datetime object, format it
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    # If it's a string, try to parse it
    try:
        from datetime import datetime
        # Try parsing ISO format or other common formats
        parsed_datetime = datetime.fromisoformat(str(value))
        return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        # If parsing fails, return the original value as a string
        return str(value)

# Register custom Jinja2 filter for timestamp conversion
@app.template_filter('timestamp')
def timestamp_filter(value):
    """Convert timestamp to human-readable format."""
    if value is None:
        return 'Unknown'
    try:
        return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Error converting timestamp {value}: {e}")
        return 'Invalid Timestamp'

# Add base64 encoding filter
@app.template_filter('b64encode')
def b64encode_filter(s):
    """
    Base64 encode the input.
    Handles both string and bytes input.
    """
    if isinstance(s, str):
        s = s.encode('utf-8')
    return base64.b64encode(s).decode('utf-8') if s else ''

def base64_encode(data):
    """Base64 encode binary data for display."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')

def json_format(data):
    """Pretty print JSON data."""
    try:
        # If it's already a dictionary, use json.dumps
        if isinstance(data, dict):
            return json.dumps(data, indent=2)
        
        # If it's a string, try to parse and format
        parsed_json = json.loads(data)
        return json.dumps(parsed_json, indent=2)
    except (TypeError, json.JSONDecodeError):
        # If it can't be parsed, return original data
        return data

def b64encode(s):
    """Base64 encode data for display in templates."""
    if s is None:
        return ''
    if isinstance(s, str):
        s = s.encode('utf-8')
    return base64.b64encode(s).decode('utf-8')

# Add custom Jinja2 filters to the application
def add_template_filters():
    """Add custom Jinja2 filters to the application."""
    app.jinja_env.filters['b64encode'] = b64encode
    app.jinja_env.filters['json_format'] = json_format

# Call the function when the app is created
add_template_filters()

@app.route('/')
@async_route
async def index():
    """Render the index page with paginated cards."""
    try:
        # Ensure parameters are integers
        page_param = request.args.get('page', '1')
        per_page_param = request.args.get('per_page', '12')
        
        try:
            page = int(page_param)
        except (ValueError, TypeError):
            page = 1
        
        try:
            per_page = int(per_page_param)
        except (ValueError, TypeError):
            per_page = 12
        
        # Ensure minimum values
        page = max(1, page)
        per_page = max(1, per_page)
        
        # Get storage and list cards
        storage = await get_storage()
        all_cards, _ = await storage.list()
        
        # Sort cards by g_time (most recent first)
        sorted_cards = sorted(all_cards, key=lambda card: getattr(card, 'g_time', 0) or 0, reverse=True)
        
        # Paginate cards
        total_items = len(sorted_cards)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        # Calculate start and end indices
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        
        current_page_cards = sorted_cards[start_index:end_index]
        
        # Process cards
        processed_cards = []
        for card in current_page_cards:
            try:
                content = card.content or b''
                if not isinstance(content, bytes):
                    content = str(content).encode('utf-8') if content is not None else b''
                
                try:
                    content_type, _ = ContentTypeInterpreter.detect_content_type(content)
                except Exception as e:
                    logger.warning(f"Content type detection error for card {card.hash}: {e}")
                    content_type = 'application/octet-stream'
                
                is_binary = not content_type.startswith('text/')
                is_image = content_type.startswith('image/')
                
                display_content = content
                if not is_binary:
                    try:
                        display_content = content.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        display_content = str(content).strip("b'")
                
                processed_cards.append({
                    'hash': card.hash,
                    'content': display_content if not is_binary else None,
                    'content_type': content_type,
                    'is_binary': is_binary,
                    'is_image': is_image,
                    'g_time': card.g_time,
                    'time_claimed': card.g_time,
                    'content_length': len(content)
                })
            except Exception as e:
                logger.error(f"Error processing card {card.hash}: {e}", exc_info=True)
                continue
        
        return render_template(
            'index.html',
            cards=processed_cards,
            page=page,
            total_pages=total_pages,
            total_items=total_items,
            per_page=per_page,
            delete_form=DeleteCardForm()
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in index view: {e}", exc_info=True)
        flash(f'An error occurred while loading the index page: {e}', 'error')
        return redirect(url_for('index'))

@app.route('/grid')
@async_route
async def grid_view():
    """Render the grid view with paginated cards."""
    try:
        # Defensive parameter extraction
        rows_param = request.args.get('rows', '3')
        cols_param = request.args.get('cols', '4')
        page_param = request.args.get('page', '1')
        
        # Parse grid-specific parameters
        rows = RequestParamHandler.parse_int_param(
            rows_param, 
            default=3, 
            min_value=1, 
            max_value=10
        )
        cols = RequestParamHandler.parse_int_param(
            cols_param, 
            default=4, 
            min_value=1, 
            max_value=10
        )
        
        # Calculate per_page based on grid dimensions
        per_page = rows * cols
        
        # Parse page parameter
        page = RequestParamHandler.parse_int_param(
            page_param, 
            default=1, 
            min_value=1
        )

        # Get storage and list cards
        storage = await get_storage()
        all_cards, _ = await storage.list()
        
        # Sort cards by g_time (most recent first)
        sorted_cards = sorted(all_cards, key=lambda card: getattr(card, 'g_time', 0) or 0, reverse=True)
        
        # Paginate cards
        current_page_cards, total_pages, total_items = RequestParamHandler.paginate(
            sorted_cards, page, per_page
        )
        
        # Process cards
        processed_cards = []
        for card in current_page_cards:
            try:
                content = card.content or b''
                if not isinstance(content, bytes):
                    content = str(content).encode('utf-8') if content is not None else b''
                
                try:
                    content_type, _ = ContentTypeInterpreter.detect_content_type(content)
                except Exception as e:
                    logger.warning(f"Content type detection error for card {card.hash}: {e}")
                    content_type = 'application/octet-stream'
                
                is_binary = not content_type.startswith('text/')
                is_image = content_type.startswith('image/')
                
                display_content = content
                if not is_binary:
                    try:
                        display_content = content.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        display_content = str(content).strip("b'")
                
                processed_cards.append({
                    'hash': card.hash,
                    'content': display_content if not is_binary else None,
                    'content_type': content_type,
                    'is_binary': is_binary,
                    'is_image': is_image,
                    'g_time': card.g_time,
                    'time_claimed': card.g_time,
                    'content_length': len(content)
                })
            except Exception as e:
                logger.error(f"Error processing card {card.hash}: {e}", exc_info=True)
                continue
        
        return render_template(
            'grid.html',
            cards=processed_cards,
            page=page,
            total_pages=total_pages,
            total_items=total_items,
            per_page=per_page,
            rows=rows,
            cols=cols,
            delete_form=DeleteCardForm()
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in grid view: {e}", exc_info=True)
        flash(f'An error occurred while loading the grid page: {e}', 'error')
        return redirect(url_for('grid_view'))

@app.route('/new_card', methods=['GET'])
def new_card():
    """Render the new card form."""
    return render_template('new_card.html', form=NewCardForm())

@app.route('/create_card', methods=['POST'])
@async_route
async def create_card():
    """Create a new card with either text or file content."""
    form = NewCardForm()
    
    if form.validate_on_submit():
        try:
            # Check if a file is uploaded
            file = form.file.data
            content = None
            card_type = form.type.data or 'default'
            
            if file:
                # If file is uploaded, prioritize file content
                content = file.read()
                # Detect content type from the uploaded file
                content_type, _ = ContentTypeInterpreter.detect_content_type(content)
            else:
                # If no file, use text content
                content = form.content.data.strip()
                # Detect content type for text content
                content_type, _ = ContentTypeInterpreter.detect_content_type(content)
            
            # Create and save the card
            card = MCard(content=content)
            
            # Save the card
            storage = await get_storage()
            await storage.save(card)
            
            # If a type was specified, log it separately
            if card_type and card_type != 'default':
                logger.info(f'Card created with type: {card_type}')
            
            flash(f'Card created successfully', 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            logger.error(f"Error creating card: {e}", exc_info=True)
            flash(f'Error creating card: {str(e)}', 'error')
    
    # If form validation fails, re-render the form with errors
    return render_template('new_card.html', form=form)

@app.route('/add_text_card', methods=['POST'])
@async_route
async def add_text_card():
    """Add a new text card."""
    form = TextCardForm()
    if form.validate_on_submit():
        try:
            content = form.content.data.strip()
            storage = await get_storage()
            card = MCard(content=content)
            await storage.save(card)
            flash('Card created successfully', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error creating text card: {e}")
            flash(f'Error creating card: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('new_card'))

@app.route('/add_file_card', methods=['POST'])
@async_route
async def add_file_card():
    """Add a new file card."""
    form = FileCardForm()
    if form.validate_on_submit():
        try:
            file = form.file.data
            if file:
                # Log file details
                logger.info(f"Uploading file: {file.filename}")
                logger.info(f"File type: {file.content_type}")
                
                # Read file content safely
                content = file.read()
                
                # Extensive logging for debugging
                logger.info(f"Raw content type: {type(content)}")
                logger.info(f"Raw content length: {len(content) if content is not None else 'N/A'}")
                
                # Ensure content is valid
                if content is None:
                    logger.error("File content is None")
                    flash("Error: Unable to read file content", 'error')
                    return redirect(url_for('new_card'))
                
                if not isinstance(content, bytes):
                    try:
                        content = content.encode('utf-8') if isinstance(content, str) else bytes(content)
                    except Exception as encode_error:
                        logger.error(f"Error converting content to bytes: {encode_error}")
                        flash(f"Error processing file: {encode_error}", 'error')
                        return redirect(url_for('new_card'))
                
                # Detect content type
                try:
                    content_type, file_ext = ContentTypeInterpreter.detect_content_type(content)
                    logger.info(f"Detected content type: {content_type}")
                    logger.info(f"Detected file extension: {file_ext}")
                except Exception as type_error:
                    logger.error(f"Error detecting content type: {type_error}")
                    content_type = 'application/octet-stream'
                    file_ext = ''
                
                storage = await get_storage()
                card = MCard(content=content)
                await storage.save(card)
                
                # Log successful upload
                logger.info(f"Uploaded file: {file.filename}, Content Type: {content_type}, Size: {len(content)} bytes, Hash: {card.hash}")
                
                flash(f'File "{file.filename}" uploaded successfully', 'success')
                return redirect(url_for('index'))
            else:
                logger.warning("No file uploaded")
                flash("Please select a file to upload", 'warning')
        except Exception as e:
            logger.error(f"Comprehensive error uploading file: {e}", exc_info=True)
            flash(f'Error uploading file: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                logger.warning(f"Form validation error - {field}: {error}")
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('new_card'))

@app.route('/view/<hash>')
@async_route
async def view_card(hash):
    """View a specific card."""
    try:
        # Log the request
        logger.info(f"View card request received for hash: {hash}")
        
        # Ensure storage is initialized
        storage = await get_storage()
        logger.info(f"Storage initialized, attempting to list cards")
        
        # Fetch all cards to find the specific card
        try:
            all_cards, _ = await storage.list()
            logger.info(f"Retrieved {len(all_cards)} cards from storage")
        except Exception as list_error:
            logger.error(f"Error listing cards: {list_error}")
            flash("Unable to retrieve cards from storage.", "error")
            return redirect(url_for('index'))
        
        # Find the card with the matching hash
        target_card = next((card for card in all_cards if card.hash == hash), None)
        
        if target_card is None:
            logger.error(f"Card with hash {hash} not found")
            flash(f"Card with hash {hash} not found.", "error")
            return redirect(url_for('index'))
        
        logger.info(f"Found card with hash {hash}, processing content")
        
        # Determine content type and handle different content types
        content = target_card.content
        
        # Ensure content is valid
        if content is None:
            content = b''
        
        # Ensure content is bytes
        if not isinstance(content, bytes):
            content = str(content).encode('utf-8') if content is not None else b''
        
        # Detect content type
        try:
            content_type, _ = ContentTypeInterpreter.detect_content_type(content)
        except Exception:
            content_type = 'application/octet-stream'
        
        is_binary = not content_type.startswith('text/')
        
        # Prepare content for display
        display_content = content
        if not is_binary:
            try:
                display_content = content.decode('utf-8').strip()
            except UnicodeDecodeError:
                display_content = str(content).strip("b'")
            
            # Additional cleaning to remove any remaining quotes or b prefix
            if display_content.startswith("'") and display_content.endswith("'"):
                display_content = display_content[1:-1]
            if display_content.startswith('"') and display_content.endswith('"'):
                display_content = display_content[1:-1]
            if display_content.startswith('b"') or display_content.startswith("b'"):
                display_content = display_content[2:-1]
        
        # Enhanced image detection
        is_image = (
            content_type.startswith('image/') or 
            (is_binary and content_type == 'application/octet-stream' and 
                (content.startswith(b'\x89PNG') or 
                 content.startswith(b'\xff\xd8\xff') or  # JPEG
                 content.startswith(b'GIF87a') or 
                 content.startswith(b'GIF89a') or 
                 content.startswith(b'RIFF') or 
                 content.startswith(b'WEBP')))
        )
        is_svg = content_type == 'image/svg+xml'
        
        # Image-specific handling
        if is_image and content_type.startswith('image/'):
            # Ensure consistent image type detection
            if content_type == 'image/jpeg' and not content.startswith(b'\xff\xd8\xff'):
                is_image = False
            elif content_type == 'image/png' and not content.startswith(b'\x89PNG'):
                is_image = False
            elif content_type == 'image/gif' and not (content.startswith(b'GIF87a') or content.startswith(b'GIF89a')):
                is_image = False
        
        # SVG content handling
        svg_content = content.decode('utf-8', errors='ignore') if is_svg else None
        
        # Ensure PDF content is handled correctly
        if content_type == 'application/pdf':
            # Verify PDF signature
            if not content.startswith(b'%PDF-'):
                logger.warning(f"Invalid PDF signature for card {hash}")
                content_type = 'application/octet-stream'
        
        # Prepare delete form
        delete_form = DeleteCardForm()
        
        # Prepare card context
        card = {
            'hash': target_card.hash,
            'content': display_content if not is_binary else None,
            'content_type': content_type,
            'is_binary': is_binary,
            'is_image': is_image,
            'is_svg': is_svg,
            'svg_content': svg_content,
            'g_time': target_card.g_time,
            'content_length': len(content)
        }
        
        logger.info(f"Rendering view_card.html template for card {hash}")
        return render_template('view_card.html', 
                             card=card,
                             delete_form=delete_form)
    
    except Exception as e:
        logger.error(f"Error while viewing card: {e}", exc_info=True)
        flash(f"An error occurred while viewing the card: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/delete/<hash>', methods=['POST'])
@async_route
async def delete_card(hash):
    """Delete a specific card."""
    try:
        logger.info(f"Attempting to delete card with hash: {hash}")
        
        # Verify CSRF token
        form = DeleteCardForm()
        if not form.validate_on_submit():
            logger.error(f"CSRF validation failed: {form.errors}")
            flash("Invalid form submission", "error")
            return redirect(url_for('index'))
        
        # Get storage and delete card
        storage = await get_storage()
        await storage.remove(hash)
        logger.info(f"Successfully deleted card {hash}")
        flash(f"Card deleted successfully.", "success")
        
    except Exception as e:
        logger.error(f"Error deleting card: {e}", exc_info=True)
        flash(f"Error deleting card: {str(e)}", "error")
    
    return redirect(url_for('index'))

@app.route('/binary/<hash>')
@async_route
async def get_binary_content(hash):
    """Retrieve binary content for a specific card."""
    try:
        # Ensure storage is initialized
        storage = await get_storage()
        
        # Find the card
        try:
            target_card = await storage.get(hash)
        except Exception as get_error:
            logger.error(f"Error retrieving card {hash}: {get_error}")
            return '', 404
        
        # Ensure content is valid
        content = target_card.content
        if content is None:
            logger.warning(f"Card {hash} has no content")
            return '', 404
        
        # Ensure content is bytes
        if not isinstance(content, bytes):
            content = str(content).encode('utf-8') if content is not None else b''
        
        # Detect content type
        try:
            content_type, _ = ContentTypeInterpreter.detect_content_type(content)
        except Exception:
            content_type = 'application/octet-stream'
        
        # Create response with appropriate headers
        response = make_response(content)
        response.headers.set('Content-Type', content_type)
        response.headers.set('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
        
        return response
    
    except Exception as e:
        logger.error(f"Error serving binary content for card {hash}: {e}", exc_info=True)
        return '', 500

@app.route('/download/<hash>')
@async_route
async def download_card(hash):
    """Download a card's content."""
    try:
        # Ensure storage is initialized
        storage = await get_storage()
        
        # Find the card
        try:
            target_card = await storage.get(hash)
        except Exception as get_error:
            logger.error(f"Error retrieving card {hash}: {get_error}")
            flash("Card not found", "error")
            return redirect(url_for('index'))
        
        # Ensure content is valid
        content = target_card.content
        if content is None:
            logger.warning(f"Card {hash} has no content")
            flash("No content available for download", "warning")
            return redirect(url_for('index'))
        
        # Ensure content is bytes
        if not isinstance(content, bytes):
            content = str(content).encode('utf-8') if content is not None else b''
        
        # Detect content type
        try:
            content_type, file_ext = ContentTypeInterpreter.detect_content_type(content)
        except Exception:
            content_type = 'application/octet-stream'
            file_ext = ''
        
        # Generate filename
        filename = f"{hash}.{file_ext}" if file_ext else f"{hash}"
        
        # Create response with appropriate headers
        response = send_file(
            io.BytesIO(content),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error downloading card {hash}: {e}", exc_info=True)
        flash("Error downloading card", "error")
        return redirect(url_for('index'))

@app.route('/thumbnail/<hash>')
@async_route
async def serve_thumbnail(hash):
    """Serve thumbnail for image content."""
    storage = await get_storage()
    try:
        # Retrieve the card
        all_cards, _ = await storage.list()
        card = next((c for c in all_cards if c.hash == hash), None)
        
        if not card or not isinstance(card.content, bytes):
            flash('Thumbnail not found', 'error')
            return redirect(url_for('index'))
        
        # Determine content type
        content_type, _ = ContentTypeInterpreter.detect_content_type(card.content)
        # Check if it's an image
        if not content_type.startswith('image/'):
            flash('Not an image', 'error')
            return redirect(url_for('index'))
        
        # Here you would typically generate a thumbnail
        # For now, just return the original image
        return send_file(
            BytesIO(card.content),
            mimetype=content_type,
            as_attachment=False
        )
    
    except Exception as e:
        app.logger.error(f'Error serving thumbnail: {str(e)}')
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/pdf/<hash>')
@async_route
async def get_pdf_content(hash):
    """Serve PDF content directly."""
    try:
        storage = await get_storage()
        target_card = await storage.get(hash)
        
        if not target_card or not target_card.content:
            return '', 404
            
        # Verify it's actually a PDF
        if not target_card.content.startswith(b'%PDF-'):
            return 'Not a valid PDF', 400
            
        response = make_response(target_card.content)
        response.headers.set('Content-Type', 'application/pdf')
        response.headers.set('Content-Disposition', 'inline')
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF content for {hash}: {e}")
        return str(e), 500

def get_file_extension(content_type):
    if content_type == 'image/jpeg':
        return '.jpg'
    elif content_type == 'image/png':
        return '.png'
    elif content_type == 'image/gif':
        return '.gif'
    elif content_type == 'image/bmp':
        return '.bmp'
    elif content_type == 'image/tiff':
        return '.tiff'
    elif content_type == 'image/webp':
        return '.webp'
    elif content_type == 'image/svg+xml':
        return '.svg'
    elif content_type == 'application/pdf':
        return '.pdf'
    elif content_type == 'text/plain':
        return '.txt'
    elif content_type == 'application/json':
        return '.json'
    elif content_type == 'application/xml':
        return '.xml'
    else:
        return ''

if __name__ == '__main__':
    # Initialize MCard before running the app
    asyncio.run(init_mcard())
    app.run(debug=DEBUG, port=PORT)
