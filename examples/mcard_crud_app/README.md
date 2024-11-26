# MCard CRUD Application

A comprehensive CRUD (Create, Read, Update, Delete) application for managing MCards, built with Flask and Bootstrap 5. This application demonstrates the capabilities of the MCard library while providing an intuitive web interface for card management.

## Features

### Core Functionality
- Create new MCards with text or file content
- View and download card content with proper content type handling
- Delete MCards from storage
- Automatic content hash generation and verification
- Binary and text content support

### Content Management
- **Intelligent Content Handling**:
  - Automatic content type detection
  - SVG content special handling with inline rendering
  - Image content with thumbnail generation
  - Binary content download support
  - Text content formatting
- **Content Type Support**:
  - Images: SVG, PNG, JPEG, GIF, and other common formats
  - Text: Plain text, JSON, and other text formats
  - Binary: Any binary content with proper MIME type detection

### User Interface
- **Clean Bootstrap 5 Design**:
  - Responsive layout for all screen sizes
  - Intuitive navigation
  - Clear content presentation
- **Card Management**:
  - Create new cards with text or file upload
  - View card details with content preview
  - Download card content
  - Delete cards with confirmation
- **Pagination**:
  - Configurable items per page
  - Page navigation controls
  - Current page indicator

## Technical Details

### Project Structure
```
mcard_crud_app/
├── app.py              # Main Flask application
├── templates/          # Jinja2 templates
│   ├── base.html      # Base template with layout
│   ├── index.html     # Main card listing
│   ├── grid.html      # Grid view layout
│   ├── new_card.html  # Card creation form
│   ├── view_card.html # Card detail view
│   └── components/    # Reusable components
└── mcard_crud.db      # SQLite database
```

### Dependencies
- **Flask**: Web application framework
- **MCard**: Core library for card management
- **Bootstrap 5**: Frontend styling and components
- **SQLite**: Database storage

### Implementation Features
- Thread-safe database connections
- Proper MIME type detection and handling
- Secure file uploads
- Error handling and user feedback
- Template inheritance for consistent UI
- Jinja2 custom filters for formatting

## Setup and Usage

1. **Installation**:
   ```bash
   # Clone the repository
   git clone [repository-url]
   cd mcard-core
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Running the Application**:
   ```bash
   cd examples/mcard_crud_app
   python app.py
   ```
   The application will be available at `http://localhost:5000`

3. **Using the Application**:
   - Visit the homepage to see existing cards
   - Click "New Card" to create a card
   - Use text input or file upload to add content
   - View, download, or delete cards from the main interface

## Development

### Adding New Features
1. Modify `app.py` for new routes and functionality
2. Add templates in the `templates` directory
3. Update static assets as needed

### Best Practices
- Use proper error handling
- Follow Flask application factory pattern
- Keep templates modular and reusable
- Maintain consistent styling
- Handle content types appropriately

## Security Notes
- The application uses a development secret key
- Implement proper security measures for production
- Validate all file uploads
- Use secure database connections
- Implement user authentication if needed
