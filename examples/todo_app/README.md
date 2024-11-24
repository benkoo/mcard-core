# MCard Todo App

A demonstration of the [[Cubical Logic Model]] ([[CLM]]) principles applied to a practical todo application. This example showcases how MCard's content-addressable storage can be integrated with modern web technologies while maintaining theoretical soundness and practical utility.

## Abstract Specification (Design Intentions)

### Context
- A web-based todo application that demonstrates MCard's capabilities as a data operating system
- Integrates natural language content (todo descriptions) with computable data (states, timestamps)
- Leverages Flask's application context for thread-safe operations
- Implements clean separation of concerns following CLM principles

### Goals
- Create a responsive, user-friendly todo management interface
- Demonstrate MCard's content-addressable storage capabilities
- Showcase proper integration with web frameworks
- Provide a foundation for more complex workflow applications
- Enable efficient search and filtering of todo items

### Success Criteria
- Thread-safe database operations
- Proper transaction management
- Comprehensive error handling
- Clean and responsive UI
- Real-time search functionality
- Efficient content display and navigation

## Concrete Implementation (Process Models)

### Technology Stack
- **Web Framework**: Flask for HTTP request handling
- **Storage System**: MCard for content-addressable storage
- **Database**: SQLite (via MCard) for persistent storage
- **Frontend**: 
  - Tailwind CSS for modern UI components
  - JSON Editor for structured data visualization
  - AJAX for dynamic content updates

### Features
1. **Card Management**
   - Create and edit todo cards
   - View detailed card content with syntax highlighting
   - Mark cards as complete/incomplete
   - Track card history and modifications

2. **Search & Navigation**
   - Real-time search functionality
   - Dynamic content filtering
   - Pagination for large datasets
   - Responsive layout for all screen sizes

3. **Content Display**
   - JSON syntax highlighting
   - Collapsible content sections
   - Copy-to-clipboard functionality
   - Dark mode support

### Data Structure
Each todo item is stored as an MCard with the following structure:
```json
{
    "title": "Todo title",
    "description": "Optional description",
    "done": false,
    "deprecated": false,
    "original_id": "hash_of_original_card",
    "clm": {
        "abstract_spec": {
            "context": "The spatial-temporal context of the todo.",
            "goals": ["A list of goal statements for the todo."],
            "success_criteria": {
                "verification": "Verification criteria for the todo.",
                "validation": "Validation criteria for the todo.",
                "performance": "Performance metrics for the todo."
            }
        },
        "concrete_impl": {
            "inputs": {},
            "activities": {},
            "outputs": {}
        },
        "realistic_expectations": {
            "practical_boundaries": {},
            "traces": ["A list of execution traces for the todo."],
            "external_feedback": {}
        }
    },
    "created_at": "timestamp",
    "updated_at": "timestamp"
}
```

### System Components
1. **Database Management**
   - Flask application context (`g`) for thread safety
   - Connection lifecycle management
   - Transaction handling with commit/rollback
   - Automatic initialization

2. **API Endpoints**
   - Create/edit todos with CLM support
   - Mark todos as complete/incomplete
   - Search and filter todos
   - View card details and history
   - Real-time content updates

3. **Frontend Interface**
   - Responsive design with Tailwind CSS
   - Dynamic search with AJAX
   - Interactive JSON editor
   - Error feedback
   - Status indicators
   - Dark mode optimization

## Setup & Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   flask --app app run --port 5002 --debug
   ```

3. Access the interface at `http://localhost:5002`

### Key Pages
- **Home** (`/`): Overview of all todo items
- **List View** (`/list`): Searchable list of all cards
- **View Card** (`/view/<hash>`): Detailed card view with JSON editor
- **Edit CLM** (`/edit_clm/<hash>`): CLM editor for todo items

## Development

### Running in Development Mode
```bash
flask --app app run --port 5002 --debug
```

### Project Structure
```
todo_app/
├── app.py              # Main Flask application
├── clm.py             # CLM implementation
├── requirements.txt    # Python dependencies
├── static/            # Static assets
├── templates/         # HTML templates
│   ├── components/    # Reusable UI components
│   ├── edit_clm.html  # CLM editor template
│   ├── index.html     # Home page
│   ├── list_all_cards.html  # Card list view
│   └── view_card.html # Card detail view
└── todo_app.db        # SQLite database
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
