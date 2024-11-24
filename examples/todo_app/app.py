from datetime import datetime
import json
import os
from flask import Flask, render_template, request, redirect, url_for, g, jsonify
from mcard.core import MCard
from mcard.storage import MCardStorage
from clm import CubicalLogicModel, AbstractSpecification, SuccessCriteria, ConcreteImplementation, RealisticExpectations
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
            print(f"Processing card: {card.content_hash} - {card.content}")  # Debug log
            todo_data = json.loads(card.content)
            
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
        
        # Return only the latest version of each todo
        todos = list(latest_todos.values())
        print(f"Returning {len(todos)} todos")  # Debug log
    except Exception as e:
        print(f"Error in index: {str(e)}")  # Debug log
        raise
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
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
            "title": title,
            "description": description,
            "done": False,
            "clm": clm.to_dict(),
            "created_at": now,
            "updated_at": now
        }

        storage = get_storage()
        print(f"Creating todo with content: {json.dumps(todo)}")  # Debug log
        card = MCard(content=json.dumps(todo))
        print(f"Created card with hash: {card.content_hash}, time_claimed: {card.time_claimed}")  # Debug log
        
        # Save to storage
        storage.save(card)
        storage.conn.commit()
        
        return redirect(url_for('index'))
    except Exception as e:
        storage.conn.rollback()
        app.logger.error(f"Error adding todo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/toggle/<card_id>', methods=['POST'])
def toggle(card_id):
    try:
        print(f"\n=== Toggling todo {card_id} ===")  # Debug log
        storage = get_storage()
        card = storage.get(card_id)
        print(f"Retrieved card: {card}")  # Debug log
        if not card:
            print(f"Card not found with ID: {card_id}")  # Debug log
            return "Todo not found", 404
        
        old_todo = json.loads(card.content)
        print(f"Original todo data: {old_todo}")  # Debug log
        
        # Create updated todo data
        updated_todo = old_todo.copy()
        updated_todo['done'] = not old_todo.get('done', False)
        updated_todo['updated_at'] = datetime.utcnow().isoformat()
        updated_todo['original_id'] = old_todo.get('original_id', card_id)  # Track the original todo ID
        updated_todo['previous_hash'] = card_id  # Track the previous version
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

@app.route('/delete/<card_id>', methods=['POST'])
def delete(card_id):
    try:
        print(f"\n=== Deleting todo {card_id} ===")  # Debug log
        storage = get_storage()
        print(f"Attempting to delete card with ID: {card_id}")  # Debug log
        if storage.delete(card_id):
            print(f"Successfully deleted card with ID: {card_id}")  # Debug log
            storage.conn.commit()
            return redirect(url_for('index'))
        else:
            print(f"Card not found with ID: {card_id}")  # Debug log
            return "Todo not found", 404
    except Exception as e:
        storage.conn.rollback()
        app.logger.error(f"Error deleting todo: {str(e)}")
        return str(e), 500

@app.route('/edit_clm/<card_id>')
def edit_clm(card_id):
    try:
        print(f"\n=== Editing CLM for card {card_id} ===")  # Debug log
        storage = get_storage()
        
        # Find the latest version of this todo
        all_cards = storage.get_all()
        latest_card = None
        latest_time = None
        
        for card in all_cards:
            todo_data = json.loads(card.content)
            original_id = todo_data.get('original_id', card.content_hash)
            
            # Check if this is the todo we're looking for
            if original_id == card_id:
                updated_at = datetime.fromisoformat(todo_data['updated_at'])
                if latest_time is None or updated_at > latest_time:
                    latest_card = card
                    latest_time = updated_at
        
        if not latest_card:
            print(f"Card not found with ID: {card_id}")  # Debug log
            return "Todo not found", 404
        
        todo = json.loads(latest_card.content)
        todo['id'] = card_id  # Use original ID for display
        todo['current_hash'] = latest_card.content_hash  # Add current hash for form submission
        print(f"Todo data: {todo}")  # Debug log
        
        if not todo.get('clm'):
            # Initialize CLM if it doesn't exist
            todo['clm'] = CubicalLogicModel.create().to_dict()
            
        return render_template('edit_clm.html', todo=todo)
    except Exception as e:
        print(f"Error in edit_clm: {str(e)}")  # Debug log
        app.logger.error(f"Error editing CLM: {str(e)}")
        return str(e), 500

@app.route('/update_clm/<card_id>', methods=['POST'])
def update_clm(card_id):
    try:
        print(f"\n=== Updating CLM for card {card_id} ===")  # Debug log
        storage = get_storage()
        card = storage.get(card_id)
        print(f"Retrieved card: {card}")  # Debug log
        if not card:
            print(f"Card not found with ID: {card_id}")  # Debug log
            return "Todo not found", 404

        old_todo = json.loads(card.content)
        print(f"Original todo data: {old_todo}")  # Debug log
        
        # Get all form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        done = request.form.get('done') == 'on'
        context = request.form.get('context', '').strip()
        goals = request.form.getlist('goals[]')
        verification = request.form.get('verification', '').strip()
        validation = request.form.get('validation', '').strip()
        performance = request.form.get('performance', '').strip()

        # Create new CLM instance
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
            concrete_impl=ConcreteImplementation.create(),
            realistic_expectations=RealisticExpectations.create()
        )

        # Create updated todo data
        updated_todo = {
            'title': title,
            'description': description,
            'done': done,
            'clm': clm.to_dict(),
            'updated_at': datetime.utcnow().isoformat(),
            'created_at': old_todo.get('created_at'),
            'original_id': old_todo.get('original_id', card_id),  # Track the original todo ID
            'previous_hash': card_id,  # Track the previous version
            'deprecated': False  # Mark this as the current version
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

if __name__ == '__main__':
    app.run(debug=True)
