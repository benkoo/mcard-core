# MCard CRUD Application

A comprehensive CRUD (Create, Read, Update, Delete) application for managing MCards, built with Flask and Bootstrap 5. This application showcases the capabilities of the MCard library while providing an intuitive and responsive interface for card management.

## Features

### Core Functionality
- Create new MCards with text or binary content
- View and manage existing MCards with rich content preview
- Delete MCards from storage
- Automatic content hash generation and verification

### Advanced Features

#### Multiple View Options
- **Table View**: Traditional list view with detailed information
  - Sortable columns
  - Compact information display
  - Quick actions per row
- **Grid View**: Visual card-based layout
  - Configurable grid dimensions (2x2 to 5x5)
  - Responsive card design
  - Visual content previews
  - Easy view switching with state preservation

#### Search and Filtering
- Real-time search functionality
- Filter by content hash and timestamp
- Case-insensitive search
- Dynamic result updates

#### Smart Pagination
- Configurable items per page (5, 10, 25, 50)
- Adaptive pagination based on view type
- Page navigation controls
- Display of current range and total items
- State preservation across view changes

#### Intelligent Content Handling
- **Automatic Content Type Detection**:
  - Images: PNG, JPEG, GIF, WebP, TIFF
  - Documents: PDF, DOCX, XLSX
  - Archives: ZIP
  - Text: Plain text, JSON, XML, HTML, PEM certificates
- Smart file extension suggestion
- MIME type detection and handling

#### Rich Content Display
- **Dynamic Content Preview**:
  - Image thumbnails with responsive sizing
  - Formatted JSON display
  - Syntax highlighting for code
  - Binary content information
- **Detailed Metadata**:
  - File type and extension
  - Content size
  - Creation timestamp
  - Content hash with copy feature

#### Modern User Interface
- Clean, responsive Bootstrap 5 design
- Interactive buttons with icons
- Visual feedback for actions
- Consistent styling across views
- Mobile-friendly layout
- Intuitive navigation between views

## Technical Details

### File Structure
```
mcard_crud_app/
├── app.py              # Main application logic
├── templates/          # HTML templates
│   ├── base.html      # Base template with common elements
│   ├── index.html     # Table view layout
│   ├── grid.html      # Grid view layout
│   ├── new_card.html  # Card creation form
│   ├── view_card.html # Card detail view
│   └── components/    # Reusable template components
└── mcard_crud.db      # SQLite database for card storage
```

### Dependencies
- **Flask**: Web framework for routing and application logic
- **Bootstrap 5**: Modern frontend framework for responsive design
- **Bootstrap Icons**: Comprehensive icon library
- **MCard Library**: Core functionality for card management
- **SQLite**: Lightweight database for persistent storage

### Implementation Details
- RESTful API architecture
- Proper error handling and validation
- Secure file handling and storage
- Efficient database operations
- Modular template design with component reuse
- Responsive UI components
- State management across view changes

## Usage

1. Start the application:
   ```bash
   python app.py
   ```

2. Access the web interface:
   - Open `http://localhost:5000` in your browser
   - Toggle between Table and Grid views using the view switcher
   - Create new cards using the "New Card" button
   - Configure grid dimensions (2-5 rows/columns) in Grid view
   - Use search and pagination to navigate large collections

## Development

### Adding New Features
1. Modify `app.py` for new routes and logic
2. Add/update templates in the templates directory
3. Follow the modular component pattern in `templates/components`
4. Maintain consistent styling with Bootstrap 5
5. Test thoroughly across different view modes

### Best Practices
- Follow RESTful routing conventions
- Implement proper error handling
- Use template inheritance for consistency
- Maintain responsive design principles
- Document new features and changes
