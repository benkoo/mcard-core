from datetime import datetime
import json
import os
from flask import Flask, render_template, request, redirect, url_for, g
from mcard.core import MCard
from mcard.collection import MCardCollection
from mcard.storage import MCardStorage

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

def get_collection():
    """Get thread-local collection instance."""
    if 'collection' not in g:
        g.collection = MCardCollection(get_storage())
    return g.collection

@app.teardown_appcontext
def teardown_db(exception):
    """Close database connection when app context ends."""
    storage = g.pop('storage', None)
    if storage is not None and hasattr(storage, 'conn'):
        storage.conn.close()

def create_todo(title, description="", done=False):
    content = {
        "title": title,
        "description": description,
        "done": done,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    content_str = json.dumps(content)
    print(f"Creating todo with content: {content_str}")  # Debug log
    card = MCard(content=content_str)
    print(f"Created card with hash: {card.content_hash}, time_claimed: {card.time_claimed}")  # Debug log
    return card

@app.route('/')
def index():
    todos = []
    print("\n=== Getting all cards ===")  # Debug log
    try:
        collection = get_collection()
        all_cards = collection.get_all_cards()
        print(f"Found {len(all_cards)} cards")  # Debug log
        for card in all_cards:
            print(f"Processing card: {card.content_hash} - {card.content}")  # Debug log
            todo_data = json.loads(card.content)
            todo_data['id'] = card.content_hash
            todos.append(todo_data)
        print(f"Returning {len(todos)} todos")  # Debug log
    except Exception as e:
        print(f"Error in index: {str(e)}")  # Debug log
        raise
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
    print("\n=== Adding new todo ===")  # Debug log
    title = request.form.get('title')
    description = request.form.get('description', '')
    print(f"Adding todo - Title: {title}, Description: {description}")  # Debug log
    
    if title:
        try:
            storage = get_storage()
            collection = get_collection()
            
            todo = create_todo(title, description)
            print(f"Created MCard with hash: {todo.content_hash}")  # Debug log
            
            # Try to save directly to storage first
            storage_result = storage.save(todo)
            print(f"Direct storage save result: {storage_result}")  # Debug log
            
            # Then add to collection
            result = collection.add_card(todo)
            print(f"Collection add result: {result}")  # Debug log
            
            # Force refresh the collection
            collection._load_cards()  # Using _load_cards() instead of refresh()
            print("Collection refreshed")  # Debug log
            
            # Verify the card was saved
            saved_card = storage.get(todo.content_hash)
            print(f"Verification - Card in storage: {saved_card is not None}")  # Debug log
            if saved_card:
                print(f"Saved card content: {saved_card.content}")  # Debug log
                
            # Commit any pending transactions
            storage.conn.commit()
            print("Storage committed")  # Debug log
        except Exception as e:
            print(f"Error in add: {str(e)}")  # Debug log
            storage.conn.rollback()  # Rollback on error
            raise
    return redirect(url_for('index'))

@app.route('/toggle/<card_id>', methods=['POST'])
def toggle(card_id):
    try:
        storage = get_storage()
        collection = get_collection()
        
        card = collection.get_card_by_hash(card_id)  # Using correct method name
        if card:
            todo_data = json.loads(card.content)
            todo_data['done'] = not todo_data['done']
            todo_data['updated_at'] = datetime.now().isoformat()
            
            # Create new card with updated content
            new_card = MCard(content=json.dumps(todo_data))
            
            # Remove old card and add new one
            collection.remove_card(card_id)
            collection.add_card(new_card)
            
            # Commit changes
            storage.conn.commit()
    except Exception as e:
        print(f"Error in toggle: {str(e)}")  # Debug log
        storage.conn.rollback()  # Rollback on error
        raise
    return redirect(url_for('index'))

@app.route('/delete/<card_id>', methods=['POST'])
def delete(card_id):
    try:
        storage = get_storage()
        collection = get_collection()
        
        collection.remove_card(card_id)
        storage.conn.commit()
    except Exception as e:
        print(f"Error in delete: {str(e)}")  # Debug log
        storage.conn.rollback()  # Rollback on error
        raise
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
