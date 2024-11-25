# MCard CRUD Application

A full-featured CRUD (Create, Read, Update, Delete) application for managing MCards, built with Flask and Bootstrap. This application demonstrates the capabilities of the MCard library while providing a user-friendly interface for card management.

## Features

### Core Functionality
- Create new MCards with text or binary content
- View existing MCards with content preview
- Delete MCards from storage
- Automatic content hash generation and verification

### Advanced Features

#### Search and Filtering
- Real-time search functionality
- Filter by content hash and timestamp
- Case-insensitive search
- Dynamic result updates

#### Pagination
- Configurable items per page (5, 10, 25, 50)
- Page navigation controls
- Display of current range and total items
- Smooth integration with search functionality

#### Content Type Detection
- Automatic file type detection for various formats:
  - Images: PNG, JPEG, GIF, WebP, TIFF
  - Documents: PDF, DOCX, XLSX
  - Archives: ZIP
  - Text: Plain text, JSON, XML, HTML, PEM certificates
- Smart file extension suggestion
- MIME type detection

#### Content Display
- Rich content preview:
  - Image preview for supported formats
  - Formatted JSON display
  - Syntax highlighting for code
  - Binary content information
- Content metadata display:
  - File type and extension
  - Content size
  - Creation timestamp
  - Content hash with copy feature

#### User Interface
- Clean, responsive Bootstrap design
- Interactive buttons and controls
- Visual feedback for actions
- Consistent styling across pages
- Mobile-friendly layout

## Technical Details

### File Structure
```
mcard_crud_app/
├── app.py              # Main application logic
├── templates/          # HTML templates
│   ├── base.html      # Base template with common elements
│   ├── index.html     # Main page with card listing
│   ├── new_card.html  # Card creation form
│   ├── view_card.html # Card detail view
│   └── hash_display.html  # Hash display component
└── mcard_crud.db      # SQLite database for card storage
```

### Dependencies
- Flask: Web framework
- Bootstrap 5: Frontend framework
- Font Awesome: Icons
- MCard Library: Core functionality

### Implementation Details
- RESTful route structure
- Proper error handling and validation
- Secure file handling
- Efficient database operations
- Modular template design
- Responsive UI components

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Access the web interface:
   - Open `http://localhost:5000` in your browser
   - Create new cards using the "New Card" button
   - View and manage existing cards in the main list
   - Use search and pagination to navigate large collections

## Development

### Adding New Features
1. Modify app.py for new routes and logic
2. Add/update templates in the templates directory
3. Update static assets as needed
4. Test thoroughly with different content types

### Best Practices
- Follow Flask application structure
- Use Bootstrap components consistently
- Handle errors gracefully
- Provide user feedback for actions
- Maintain responsive design
- Document new features

## Security Considerations
- Input validation for all forms
- Safe file handling for binary content
- Protection against common web vulnerabilities
- Proper error message handling
