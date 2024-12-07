# MCard CRUD Application

A comprehensive CRUD (Create, Read, Update, Delete) application for managing MCards, built with Flask and Bootstrap 5. This application demonstrates the capabilities of the MCard library while providing an intuitive web interface for card management.

## Key Features
- Asynchronous content storage using MCard
- Support for multiple content types (text, binary, SVG)
- Timestamp tracking with `g_time`
- Flexible content management
- Dual view modes: Grid and Table layouts
- PDF content support with inline viewer
- A search field for quick card lookup with interactivity

### Core Functionality
- Create new MCards with text or file content
- View and download card content with proper content type handling
- Delete MCards from storage
- Automatic content hash generation and verification
- Binary and text content support
- Switch between grid and table views

### Content Management
- **Intelligent Content Handling**:
  - Automatic content type detection
  - SVG content special handling with inline rendering
  - Image content with thumbnail generation
  - PDF content with built-in viewer
  - Binary content download support
  - Text content formatting
- **Content Type Support**:
  - Images: SVG, PNG, JPEG, GIF, and other common formats
  - Documents: PDF with inline viewer
  - Text: Plain text, JSON, and other text formats
  - Binary: Any binary content with proper MIME type detection

## Views and Navigation
- **Table View**:
  - Compact list view with columns for preview, type, hash, g_time
  - Quick access to view and delete actions
  - Sortable columns
- **Grid View**:
  - Visual card-based layout
  - Large content previews
  - Metadata display
  - Action buttons for each card

## Endpoints
- `/`: List all cards with view mode toggle
- `/view/<hash>`: View a specific card's content
- `/delete/<hash>`: Delete a specific card
- `/get_binary_content/<hash>`: Retrieve binary content
- `/thumbnail/<hash>`: Get a thumbnail of the content
- `/pdf/<hash>`: Serve PDF content directly

## Timestamp Handling
The application uses the `g_time` attribute from MCard to track content creation time. This attribute:
- Represents the global timestamp of content creation
- Is automatically generated when a card is created
- Used consistently across all views (table, grid, and detail)
- Formatted using a custom datetime filter

### Timestamp Display
- Consistent formatting across all views
- Uses custom Jinja2 datetime filter
- Handles both datetime objects and timestamp strings
- Fallback to 'Unknown' for missing timestamps

## Content Types Supported
- Plain Text with syntax highlighting
- PDF Documents with inline viewer
- Images (PNG, JPEG, GIF, WebP)
- SVG Graphics with inline rendering
- Binary Files with download option
- Dynamically detected content types

## Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`

## Key Technologies
- Python 3.12
- Flask with async support
- MCard Library
- PDF.js for PDF viewing
- Bootstrap 5 for UI
- Font Awesome icons

## Recent Updates
- Added PDF content support with inline viewer
- Implemented grid/table view toggle
- Enhanced timestamp display consistency
- Fixed View button functionality
- Improved error handling and logging
- Updated UI components for better user experience

## Roadmap
- [ ] Add advanced filtering
- [ ] Implement content search
- [ ] Enhance timestamp-based operations
- [ ] Add batch operations for multiple cards
- [ ] Implement card content editing
