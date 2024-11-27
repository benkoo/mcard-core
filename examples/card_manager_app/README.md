# Card Manager App

## Overview
The Card Manager App is a web application that provides a user-friendly interface for managing MCard data. It's built using Flask for server-side rendering and integrates directly with the MCard API (`mcard/interfaces/api/mcard_api.py`) as its backend data source. This ensures consistent data handling and reliable card management operations.

## Features

### Card Management
- Create new cards with text or binary content
- View cards in a grid or list layout
- Delete existing cards
- Detailed view of individual cards
- Support for various content types (text, images, PDFs, binary)
- Automatic content type detection
- Download functionality for binary content

### UI/UX Features
- Responsive grid/list view switching
- Pagination support with configurable items per page
- Modern, clean interface with Tailwind CSS
- Interactive drag-and-drop file upload
- Content preview with format-specific rendering
- Flash messages for operation feedback

## Application Structure

### Routes
- **Home** (`/`): Main page with paginated card catalog
- **Card Catalog** (`/catalog`): Alternative view of all cards
- **New Card** (`/new_card`): Interface for card creation
- **Card Detail** (`/card/<hash>`): Detailed view of a specific card
- **Card Operations** (`/cards/<hash>`): RESTful endpoint for card operations (DELETE)

### Components
1. **Base Components**
   - `base.html`: Base template with navigation and layout structure
   - `nav_bar.html`: Navigation component with responsive design

2. **Card Display Components**
   - `multi_card_container.html`: Grid/list view of multiple cards
   - `single_card_container.html`: Detailed card view
   - `card_content_display.html`: Content rendering macro

3. **Input Components**
   - `content_submission_container.html`: Card creation form with tabs for text/binary input

### Backend Integration
The application communicates with the MCard API using the following endpoints:
- **GET** `/cards/`: Retrieve all cards
- **GET** `/cards/<hash>`: Get specific card
- **POST** `/cards/`: Create new card
- **DELETE** `/cards/<hash>`: Delete card

### Directory Structure
```
card_manager_app/
├── app.py                 # Flask application entry point
├── requirements.txt       # Python dependencies
├── start.sh              # Application startup script
├── .env                  # Environment configuration
└── templates/
    ├── base.html         # Base template
    ├── nav_bar.html      # Navigation component
    ├── index.html        # Home page
    ├── card_catalog_page.html    # Catalog view
    ├── new_card_page.html        # Card creation
    ├── single_card_page.html     # Card detail view
    ├── content_submission_container.html  # Card creation form
    ├── multi_card_container.html         # Grid/list view
    ├── single_card_container.html        # Detail view
    └── macros/
        └── card_content_display.html     # Content rendering

## Recent Updates
1. **RESTful API Alignment**
   - Updated card deletion to use proper DELETE method
   - Changed URL patterns to follow REST conventions
   - Improved error handling and response formats

2. **Pagination Improvements**
   - Added pagination support to all card list views
   - Implemented configurable items per page
   - Added page navigation controls

3. **UI Enhancements**
   - Added grid/list view switching
   - Improved content type detection and display
   - Enhanced navigation with proper routing
   - Added flash messages for better user feedback

## Technologies Used
- **Flask**: Web framework for routing and templating
- **Python Requests**: API communication
- **Jinja2**: Template engine
- **Tailwind CSS**: Styling and responsive design
- **JavaScript**: Interactive features and async operations

## Configuration
The application uses environment variables for configuration:
- `FLASK_SECRET_KEY`: Session security
- `MCARD_API_KEY`: API authentication
- `API_BASE_URL`: MCard API endpoint

## Development Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Run the application: `./start.sh`

## Error Handling
- Comprehensive error handling for API communication
- User-friendly error messages
- Graceful fallbacks for missing data
- Proper HTTP status codes
