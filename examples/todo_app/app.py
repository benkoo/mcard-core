from datetime import datetime
import json
import os
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, Response
from mcard.core import MCard
from mcard.storage import MCardStorage
from clm import CubicalLogicModel, AbstractSpecification, SuccessCriteria, ConcreteImplementation, RealisticExpectations
from clm import CubicalLogicModel
import uuid

app = Flask(__name__)

# Initialize database path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo_app.db")
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
    if storage is not None and hasattr(storage, 'conn'):
        storage.conn.close()

@app.template_filter('datetime')
def format_datetime(value):
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return value

@app.route('/')
def index():
    todos = []
    print("\n=== Getting all cards ===")  # Debug log
    try:
        storage = get_storage()
        all_cards = storage.get_all()
        print(f"Found {len(all_cards)} cards")  # Debug log
        
        # Track the latest non-deprecated version of each todo
        latest_todos = {}
        for card in all_cards:
            print(f"Processing card: {card.content_hash} - {card.content[:100]}")  # Debug log truncated content
            
            # Skip binary cards
            try:
                # First try to decode as UTF-8 to check if it's text
                try:
                    content_str = card.content.decode('utf-8') if isinstance(card.content, bytes) else card.content
                except UnicodeDecodeError:
                    print(f"Skipping binary card: {card.content_hash}")  # Debug log
                    continue

                # Try to parse as JSON
                todo_data = json.loads(content_str)
                
                # Skip metadata cards and non-todo cards
                if not isinstance(todo_data, dict) or 'title' not in todo_data:
                    print(f"Skipping non-todo card: {card.content_hash}")  # Debug log
                    continue
                
                # Skip deprecated cards
                if todo_data.get('deprecated', False):
                    print(f"Skipping deprecated card: {card.content_hash}")  # Debug log
                    continue
                    
                # If this is an update to a previous todo, use the original ID
                original_id = todo_data.get('original_id', card.content_hash)
                todo_data['id'] = original_id
                
                # Keep track of the latest version of each todo
                if original_id not in latest_todos or todo_data['updated_at'] > latest_todos[original_id]['updated_at']:
                    latest_todos[original_id] = todo_data
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"Skipping non-JSON card: {card.content_hash}")  # Debug log
                continue
        
        # Return only the latest version of each todo
        todos = list(latest_todos.values())
        print(f"Returning {len(todos)} todos")  # Debug log
    except Exception as e:
        print(f"Error in index: {str(e)}")  # Debug log
        raise
    return render_template('index.html', todos=todos)

def check_duplicate_content(storage, content):
    """Check if content already exists in storage."""
    # Get content hash without saving
    temp_card = MCard(content=content)
    content_hash = temp_card.content_hash
    
    # Get all cards and check for matching content hash
    all_cards = storage.get_all()
    for card in all_cards:
        if card.content_hash == content_hash:
            # Get metadata for this card
            try:
                metadata_card = storage.get(card.content_hash)
                if metadata_card:
                    # Format the time in a readable way
                    time_str = metadata_card.time_claimed.strftime("%Y-%m-%d %H:%M:%S")
                    metadata = {
                        "found": True,
                        "content_hash": card.content_hash,
                        "time_claimed": time_str,
                        "size": len(card.content) if isinstance(card.content, bytes) else len(card.content.encode('utf-8'))
                    }
                    print(f"Found duplicate with metadata: {metadata}")  # Debug log
                    return metadata
            except Exception as e:
                print(f"Error getting metadata: {e}")
    return {"found": False}

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
                response = {
                    "warning": "Same content was found, no new MCard created",
                    "metadata": duplicate_check
                }
                print(f"Sending duplicate response: {response}")  # Debug log
                return jsonify(response), 409
                
            # Create metadata for text content
            metadata = {
                "content_type": "text/plain",
                "size": len(content),
                "encoding": "utf-8",
                "filename": "text.txt"
            }
            
            # Store text content
            card = MCard(content=content)
            storage.save(card)
            
            # Create metadata card
            metadata["text_hash"] = card.content_hash
            metadata_card = MCard(content=json.dumps(metadata))
            storage.save(metadata_card)
            storage.conn.commit()
            
            print(f"Stored text content with metadata hash: {metadata_card.content_hash} and text hash: {card.content_hash}")  # Debug log
            return redirect(url_for('view_card', content_hash=metadata_card.content_hash))
            
        # Check if this is a file upload
        if 'file' in request.files:
            file = request.files['file']
            print(f"\n=== File Upload Debug ===")
            print(f"File object: {file}")
            print(f"Original filename: {file.filename}")
            
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Get the file content and metadata
            content = file.read()
            content_type = file.content_type or 'application/octet-stream'
            filename = file.filename
            
            print(f"Uploading file: {filename}")
            print(f"Content type: {content_type}")
            print(f"Content size: {len(content)} bytes")
            if isinstance(content, bytes):
                print(f"First 20 bytes: {' '.join([f'{b:02x}' for b in content[:20]])}")
            
            # Check for duplicates
            duplicate_check = check_duplicate_content(storage, content)
            if duplicate_check["found"]:
                response = {
                    "warning": "Same content was found, no new MCard created",
                    "metadata": duplicate_check
                }
                print(f"Sending duplicate response for file: {response}")
                return jsonify(response), 409
            
            # For text files, store as UTF-8 text
            if content_type.startswith('text/') or content_type == 'application/json':
                try:
                    # Try to decode as text
                    content_str = content.decode('utf-8') if isinstance(content, bytes) else content
                    metadata = {
                        "content_type": content_type,
                        "size": len(content_str),
                        "encoding": "utf-8",
                        "filename": filename
                    }
                    
                    # Store text content directly
                    card = MCard(content=content_str)
                    storage.save(card)
                    
                    # Create a metadata card
                    metadata["text_hash"] = card.content_hash
                    metadata_card = MCard(content=json.dumps(metadata))
                    storage.save(metadata_card)
                    storage.conn.commit()
                    
                    print(f"Stored text file:")
                    print(f"- Metadata hash: {metadata_card.content_hash}")
                    print(f"- Text hash: {card.content_hash}")
                    return redirect(url_for('view_card', content_hash=metadata_card.content_hash))
                except UnicodeDecodeError:
                    # If decoding fails, treat as binary
                    print("Failed to decode as text, treating as binary")
                    content_type = 'application/octet-stream'
            
            # Store binary content first
            binary_card = MCard(content=content)
            print(f"\n=== Storing Binary Content ===")
            print(f"Content type: {content_type}")
            print(f"Content size: {len(content)} bytes")
            if len(content) >= 20:
                hex_bytes = ' '.join([f'{b:02x}' for b in content[:20]])
                print(f"First 20 bytes (hex): {hex_bytes}")
            storage.save(binary_card)
            storage.conn.commit()  # Commit after saving binary content
            print(f"Stored binary content with hash: {binary_card.content_hash}")
            
            # Create a metadata wrapper for binary data
            metadata = {
                "content_type": content_type,
                "size": len(content),
                "encoding": "binary",
                "filename": filename,
                "binary_hash": binary_card.content_hash
            }
            
            print(f"Created metadata: {metadata}")
            
            # Create a metadata card linking to the binary data
            metadata_card = MCard(content=json.dumps(metadata))
            storage.save(metadata_card)
            storage.conn.commit()
            
            print(f"Stored file:")
            print(f"- Metadata hash: {metadata_card.content_hash}")
            print(f"- Binary hash: {binary_card.content_hash}")
            
            # Redirect to view page
            return redirect(url_for('view_card', content_hash=metadata_card.content_hash))
            
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
            
            # Get filename from Content-Disposition header or fallback to a default
            filename = None
            content_disposition = request.headers.get('Content-Disposition')
            if content_disposition:
                import re
                filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)
            
            if not filename:
                # Try to guess extension from content type
                ext = mimetypes.guess_extension(content_type) or ''
                filename = f'file{ext}'
            
            # Create a metadata wrapper for binary data
            metadata = {
                "content_type": content_type,
                "size": len(content),
                "encoding": "binary",
                "filename": filename
            }
            
            # Store binary data directly
            card = MCard(content=content)
            storage.save(card)
            
            # Create a metadata card linking to the binary data
            metadata["binary_hash"] = card.content_hash
            metadata_card = MCard(content=json.dumps(metadata))
            storage.save(metadata_card)
            storage.conn.commit()
            
            return redirect(url_for('view_card', content_hash=metadata_card.content_hash))

        # Handle JSON and text data
        storage = get_storage()
        card = MCard(content=content_str)
        storage.save(card)
        storage.conn.commit()
        return redirect(url_for('view_card', content_hash=card.content_hash))
        
    except Exception as e:
        if 'storage' in locals():
            storage.conn.rollback()
        app.logger.error(f"Error adding card: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/todo/add', methods=['POST'])
def add_todo_card():
    """Specific route for adding todo cards with CLM support."""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        context = request.form.get('context', '').strip()
        goals = request.form.getlist('goals[]')
        
        # Create CLM instance with provided data
        clm = CubicalLogicModel.create(context=context, goals=goals)
        
        # Create todo with timestamp and CLM
        now = datetime.utcnow().isoformat()
        todo = {
            "type": "todo",
            "title": title,
            "description": description,
            "done": False,
            "clm": clm.to_dict(),
            "created_at": now,
            "updated_at": now
        }

        # Create a new request context for the internal API call
        with app.test_request_context(
            '/api/cards',
            method='POST',
            content_type='application/json',
            data=json.dumps(todo)
        ) as ctx:
            ctx.push()
            response = add_card()
            ctx.pop()

            if isinstance(response, tuple):
                response_data, status_code = response
                if status_code != 200:
                    raise Exception(response_data.get('error', 'Unknown error occurred'))
            
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error adding todo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/toggle/<content_hash>', methods=['POST'])
def toggle(content_hash):
    try:
        print(f"\n=== Toggling todo {content_hash} ===")  # Debug log
        storage = get_storage()
        card = storage.get(content_hash)
        print(f"Retrieved card: {card}")  # Debug log
        if not card:
            print(f"Card not found with ID: {content_hash}")  # Debug log
            return "Todo not found", 404
        
        old_todo = json.loads(card.content)
        print(f"Original todo data: {old_todo}")  # Debug log
        
        # Create updated todo data
        updated_todo = old_todo.copy()
        updated_todo['done'] = not old_todo.get('done', False)
        updated_todo['updated_at'] = datetime.utcnow().isoformat()
        updated_todo['original_id'] = old_todo.get('original_id', content_hash)  # Track the original todo ID
        updated_todo['previous_hash'] = content_hash  # Track the previous version
        updated_todo['deprecated'] = False  # Mark this as the current version
        print(f"Updated todo data: {updated_todo}")  # Debug log
        
        # Create new card with updated content
        new_card = MCard(content=json.dumps(updated_todo))
        print(f"Created new card with hash: {new_card.content_hash}")  # Debug log
        
        # Mark the old card as deprecated
        old_todo['deprecated'] = True
        card.content = json.dumps(old_todo)
        
        # Save both cards
        storage.save(card)  # Save deprecated old card
        storage.save(new_card)  # Save new card
        storage.conn.commit()
        print(f"Successfully saved new card and deprecated old card")  # Debug log
        
        return redirect(url_for('index'))
    except Exception as e:
        storage.conn.rollback()
        app.logger.error(f"Error toggling todo: {str(e)}")
        return str(e), 500

@app.route('/delete/<content_hash>', methods=['POST'])
def delete(content_hash):
    try:
        print(f"\n=== Deleting todo {content_hash} ===")  # Debug log
        storage = get_storage()
        print(f"Attempting to delete card with ID: {content_hash}")  # Debug log
        if storage.delete(content_hash):
            print(f"Successfully deleted card with ID: {content_hash}")  # Debug log
            storage.conn.commit()
            return redirect(url_for('list_all_cards'))
        else:
            print(f"Card not found with ID: {content_hash}")  # Debug log
            return "Todo not found", 404
    except Exception as e:
        storage.conn.rollback()
        app.logger.error(f"Error deleting todo: {str(e)}")
        return str(e), 500

@app.route('/edit_clm/<content_hash>')
def edit_clm(content_hash):
    try:
        print(f"\n=== Editing CLM for card {content_hash} ===")  # Debug log
        storage = get_storage()
        card = storage.get(content_hash)
        
        if not card:
            print(f"Card not found with ID: {content_hash}")  # Debug log
            return "Todo not found", 404

        try:
            todo = json.loads(card.content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse card content as JSON: {e}")  # Debug log
            return "Invalid card content", 400

        print(f"Card content parsed successfully: {todo}")  # Debug log
        
        # Initialize CLM if it doesn't exist
        if not todo.get('clm'):
            print("Initializing CLM data")  # Debug log
            todo['clm'] = CubicalLogicModel.create().to_dict()
            # Save the updated content back to storage
            storage.update(card.content_hash, json.dumps(todo))
            storage.conn.commit()
        
        todo['id'] = content_hash  # Use original ID for display
        todo['current_hash'] = card.content_hash  # Add current hash for form submission
        print(f"Final todo data with CLM: {todo}")  # Debug log
        
        return render_template('edit_clm.html', todo=todo)
    except Exception as e:
        print(f"Error in edit_clm: {str(e)}")  # Debug log
        app.logger.error(f"Error editing CLM: {str(e)}")
        return str(e), 500

@app.route('/update_clm/<content_hash>', methods=['POST'])
def update_clm(content_hash):
    try:
        print(f"\n=== Updating CLM for card {content_hash} ===")  # Debug log
        storage = get_storage()
        card = storage.get(content_hash)
        print(f"Retrieved card: {card}")  # Debug log
        if not card:
            print(f"Card not found with ID: {content_hash}")  # Debug log
            return "Todo not found", 404

        old_todo = json.loads(card.content)
        print(f"Original todo data: {old_todo}")  # Debug log
        
        # Get basic form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        done = request.form.get('done') == 'true'

        # Get Abstract Specification data
        context = request.form.get('abstract_spec.context', '').strip()
        goals = [g.strip() for g in request.form.get('abstract_spec.goals', '').split('\n') if g.strip()]
        verification = request.form.get('abstract_spec.success_criteria.verification', '').strip()
        validation = request.form.get('abstract_spec.success_criteria.validation', '').strip()
        performance = request.form.get('abstract_spec.success_criteria.performance', '').strip()

        # Get Concrete Implementation data
        try:
            inputs = json.loads(request.form.get('concrete_impl.inputs', '[]'))
            activities = json.loads(request.form.get('concrete_impl.activities', '[]'))
            outputs = json.loads(request.form.get('concrete_impl.outputs', '[]'))
        except json.JSONDecodeError:
            inputs, activities, outputs = [], [], []

        # Get Realistic Expectations data
        try:
            practical_boundaries = json.loads(request.form.get('realistic_expectations.practical_boundaries', '[]'))
            traces = [t.strip() for t in request.form.get('realistic_expectations.traces', '').split('\n') if t.strip()]
            external_feedback = json.loads(request.form.get('realistic_expectations.external_feedback', '[]'))
        except json.JSONDecodeError:
            practical_boundaries, external_feedback = [], []

        # Create new CLM instance with all fields
        clm = CubicalLogicModel(
            abstract_spec=AbstractSpecification(
                context=context,
                goals=goals,
                success_criteria=SuccessCriteria(
                    verification=verification,
                    validation=validation,
                    performance=performance
                )
            ),
            concrete_impl=ConcreteImplementation(
                inputs=inputs,
                activities=activities,
                outputs=outputs
            ),
            realistic_expectations=RealisticExpectations(
                practical_boundaries=practical_boundaries,
                traces=traces,
                external_feedback=external_feedback
            )
        )

        # Create updated todo data
        updated_todo = {
            'title': title,
            'description': description,
            'done': done,
            'clm': clm.to_dict(),
            'updated_at': datetime.utcnow().isoformat(),
            'created_at': old_todo.get('created_at'),
            'original_id': old_todo.get('original_id', content_hash),
            'previous_hash': content_hash,
            'deprecated': False
        }
        print(f"Updated todo data: {updated_todo}")  # Debug log

        # Create new card with updated content
        new_card = MCard(content=json.dumps(updated_todo))
        print(f"Created new card with hash: {new_card.content_hash}")  # Debug log
        
        # Mark the old card as deprecated
        old_todo['deprecated'] = True
        card.content = json.dumps(old_todo)
        
        # Save both cards
        storage.save(card)  # Save deprecated old card
        storage.save(new_card)  # Save new card
        storage.conn.commit()
        print(f"Successfully saved new card and deprecated old card")  # Debug log

        return redirect(url_for('index'))
    except Exception as e:
        storage.conn.rollback()
        print(f"Error in update_clm: {str(e)}")  # Debug log
        app.logger.error(f"Error updating CLM: {str(e)}")
        return str(e), 500

@app.route('/new_card')
def new_card():
    """Route to display the new card creation page."""
    return render_template('new_card.html')

@app.route("/api/search_cards")
def search_cards():
    search_query = request.args.get('search', '').strip()
    per_page = request.args.get('per_page', 7, type=int)
    page = request.args.get('page', 1, type=int)

    storage = get_storage()
    all_cards = storage.get_all()
    todos = []
    
    # Convert cards to todo format
    for card in all_cards:
        todo_data = {
            'id': card.content_hash,
            'time_claimed': card.time_claimed
        }
        todos.append(todo_data)
    
    # Sort by time_claimed timestamp, most recent first
    todos.sort(key=lambda x: x.get('time_claimed', ''), reverse=True)
    
    # Apply search filter if query exists and is not empty
    if search_query and len(search_query) >= 2:
        todos = [todo for todo in todos if 
                search_query.lower() in str(todo['id']).lower() or 
                search_query.lower() in str(todo['time_claimed']).lower()]
    
    # Calculate pagination
    total_items = len(todos)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get current page items
    current_items = todos[start_idx:end_idx]
    
    return jsonify({
        'todos': current_items,
        'total_pages': total_pages,
        'current_page': page
    })

@app.route("/list_all_cards")
def list_all_cards():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 7, type=int)
    search_query = request.args.get('search', '').strip()

    storage = get_storage()
    all_cards = storage.get_all()
    todos = []
    
    # Convert cards to todo format
    for card in all_cards:
        todo_data = {
            'id': card.content_hash,
            'time_claimed': card.time_claimed
        }
        todos.append(todo_data)
    
    # Sort by time_claimed timestamp, most recent first
    todos.sort(key=lambda x: x.get('time_claimed', ''), reverse=True)
    
    # Apply search filter if query exists
    if search_query:
        todos = [todo for todo in todos if 
                search_query.lower() in str(todo['id']).lower() or 
                search_query.lower() in str(todo['time_claimed']).lower()]
    
    # Calculate pagination
    total_items = len(todos)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get current page items
    current_items = todos[start_idx:end_idx]
    
    return render_template(
        "list_all_cards.html",
        todos=current_items,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page,
        search_query=search_query
    )

@app.route('/view/<content_hash>')
def view_card(content_hash):
    """Display a card's content, handling both text and binary data."""
    try:
        storage = get_storage()
        card = storage.get(content_hash)
        if not card:
            return "Card not found", 404

        print(f"\n=== View Card Debug ===")
        print(f"Content hash: {content_hash}")
        print(f"Content type: {type(card.content)}")
        if isinstance(card.content, bytes):
            print(f"First few bytes: {card.content[:20]}")
        else:
            print(f"Content preview: {str(card.content)[:100]}")

        # Try to parse as JSON first
        content_type = 'application/octet-stream'  # Default content type
        try:
            if isinstance(card.content, str):
                content = json.loads(card.content)
                print(f"Successfully parsed JSON content: {str(content)[:200]}")
                
                # Check if this is a binary metadata card
                if isinstance(content, dict) and content.get('encoding') == 'binary':
                    print(f"Found binary metadata card")
                    binary_hash = content.get('binary_hash')
                    print(f"Binary hash from metadata: {binary_hash}")
                    # Get the binary card to verify it exists
                    binary_card = storage.get(binary_hash)
                    if not binary_card:
                        print(f"Binary content not found for hash: {binary_hash}")
                        return "Binary content not found", 404
                    print(f"Found binary content, size: {len(binary_card.content)} bytes")
                    return render_template('view_card.html',
                                        content_hash=binary_hash,  # Use the binary hash for viewing
                                        time_claimed=card.time_claimed,
                                        content=content,
                                        content_type=content.get('content_type', content_type),
                                        filename=content.get('filename'),
                                        is_binary=True)
                
                # For todo cards, ensure CLM exists
                if isinstance(content, dict) and content.get('type') == 'todo':
                    if not content.get('clm'):
                        content['clm'] = CubicalLogicModel.create().to_dict()
                        # Save the updated content back to storage
                        storage.update(card.content_hash, json.dumps(content))
                        storage.conn.commit()
                
                # For all JSON content, convert to formatted string
                content_str = json.dumps(content, indent=2)
                return render_template('view_card.html', 
                                    content_hash=card.content_hash,
                                    time_claimed=card.time_claimed,
                                    content=content_str,
                                    is_binary=False)
                
            else:
                print(f"Content is not a string, treating as binary")
                # For binary content, detect type directly
                if isinstance(card.content, bytes):
                    if card.content.startswith(b'\x89PNG\r\n\x1a\n'):
                        content_type = 'image/png'
                        print("Detected PNG image")
                    elif card.content.startswith(b'\xff\xd8\xff'):
                        content_type = 'image/jpeg'
                        print("Detected JPEG image")
                    elif card.content.startswith(b'GIF87a') or card.content.startswith(b'GIF89a'):
                        content_type = 'image/gif'
                        print("Detected GIF image")
                    elif card.content.startswith(b'RIFF') and card.content[8:12] == b'WEBP':
                        content_type = 'image/webp'
                        print("Detected WebP image")
                
                print(f"Content type detected: {content_type}")
                print(f"Content length: {len(card.content)} bytes")
                
                # For binary files, pass the content type and hash
                return render_template('view_card.html',
                                    content_hash=card.content_hash,
                                    time_claimed=card.time_claimed,
                                    content={"size": len(card.content)},
                                    is_binary=True,
                                    content_type=content_type)
                
        except json.JSONDecodeError:
            print("Failed to parse JSON, checking if binary")
            # If we get here, it's either binary content or plain text
            if isinstance(card.content, bytes):
                # Try to detect content type from the first few bytes
                if card.content.startswith(b'\x89PNG\r\n\x1a\n'):
                    content_type = 'image/png'
                    print("Detected PNG image")
                elif card.content.startswith(b'\xff\xd8\xff'):
                    content_type = 'image/jpeg'
                    print("Detected JPEG image")
                elif card.content.startswith(b'GIF87a') or card.content.startswith(b'GIF89a'):
                    content_type = 'image/gif'
                    print("Detected GIF image")
                elif card.content.startswith(b'RIFF') and len(card.content) >= 12 and card.content[8:12] == b'WEBP':
                    content_type = 'image/webp'
                    print("Detected WebP image")
                    print(f"Content length: {len(card.content)} bytes")
                    print(f"First 20 bytes: {' '.join([f'{b:02x}' for b in card.content[:20]])}")

        # Handle plain text content
        return render_template('view_card.html', 
                            content_hash=card.content_hash,
                            time_claimed=card.time_claimed,
                            content=card.content,
                            is_binary=False)
            
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

        print(f"Content type: {type(content)}")
        if isinstance(content, str):
            print(f"Content preview: {str(content)[:100]}")
            # Try to parse as JSON to check if this is a metadata card
            try:
                metadata = json.loads(content)
                print(f"Parsed metadata: {metadata}")
                if isinstance(metadata, dict) and metadata.get('encoding') == 'binary':
                    # This is a metadata card, get the actual binary content
                    content_type = metadata.get("content_type", "application/octet-stream")
                    filename = metadata.get("filename", "file")
                    binary_hash = metadata.get("binary_hash")
                    print(f"Found binary metadata - type: {content_type}, filename: {filename}, binary_hash: {binary_hash}")
                    binary_card = storage.get(binary_hash)
                    if binary_card:
                        content = binary_card.content
                        print(f"Retrieved binary content, size: {len(content)} bytes")
                        if isinstance(content, bytes):
                            hex_bytes = ' '.join([f'{b:02x}' for b in content[:20]])
                            print(f"Binary content first 20 bytes (hex): {hex_bytes}")
                    else:
                        print(f"Binary content not found for hash: {binary_hash}")
                        return "Binary content not found", 404
            except json.JSONDecodeError:
                print("Not a JSON card, treating as raw binary content")
        
        if isinstance(content, bytes):
            # Print first 20 bytes in hex for debugging
            hex_bytes = ' '.join([f'{b:02x}' for b in content[:20]])
            print(f"First 20 bytes (hex): {hex_bytes}")
            if len(content) >= 12:  # WebP needs at least 12 bytes
                riff = content.startswith(b'RIFF')
                webp = content[8:12] == b'WEBP'
                print(f"RIFF header present: {riff}")
                print(f"WEBP identifier present: {webp}")

            # Try to detect content type from the first few bytes
            if content.startswith(b'\x89PNG\r\n\x1a\n'):
                content_type = 'image/png'
                print("Detected PNG image")
            elif content.startswith(b'\xff\xd8\xff'):
                content_type = 'image/jpeg'
                print("Detected JPEG image")
            elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
                content_type = 'image/gif'
                print("Detected GIF image")
            elif content.startswith(b'RIFF') and len(content) >= 12 and content[8:12] == b'WEBP':
                content_type = 'image/webp'
                print("Detected WebP image")
                print(f"Content length: {len(content)} bytes")
                print(f"First 20 bytes: {' '.join([f'{b:02x}' for b in content[:20]])}")

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

if __name__ == '__main__':
    app.run(debug=True)
