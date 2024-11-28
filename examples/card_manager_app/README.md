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
- Rate-limited search with debouncing (prevents excessive API calls while typing)
- Dynamic grid column adjustment

## Application Structure

### Routes
- **Home** (`/`): Main page with paginated card catalog
- **Card Catalog** (`/catalog`): Alternative view of all cards
- **New Card** (`/new_card`): Interface for card creation
- **Card Detail** (`/card/<hash>`): Detailed view of a specific card
- **Card Operations** (`/cards/<hash>`): RESTful endpoint for card operations (DELETE)
- **Search** (`/search`): AJAX endpoint for card search with pagination

### Components
1. **Base Components**
   - `base.html`: Base template with navigation and layout structure
   - `nav_bar.html`: Navigation component with responsive design

2. **Card Display Components**
   - `multi_card_container.html`: Main container with search and display controls
     - Search bar with debounced input
     - Grid column adjustment
     - Items per page selector
   - `card_list.html`: Self-contained card grid component
     - Card grid layout with dynamic columns
     - Integrated pagination controls
     - Individual card display and actions
   - `single_card_container.html`: Detailed card view
   - `card_content_display.html`: Content rendering macro

3. **Utility Components**
   - `pagination.html`: Reusable pagination macro
     - Page navigation controls
     - Items per page integration
     - Support for additional URL parameters

4. **Input Components**
   - `content_submission_container.html`: Card creation form with tabs for text/binary input

### Component Organization
The application follows a modular component structure:

1. **Container-Content Pattern**
   - `multi_card_container.html` acts as a layout container
   - Handles search and display controls
   - Delegates card rendering to `card_list.html`

2. **Self-Contained Card List**
   - `card_list.html` is a complete component
   - Manages its own pagination
   - Handles card grid layout and individual card rendering
   - Can be reused in different contexts

3. **Search Integration**
   - Search functionality is implemented in the container
   - Uses debouncing to prevent excessive API calls
   - Maintains pagination state during search
   - Updates only the card list content when searching

### Backend Integration
The application communicates with the MCard API using the following endpoints:
- **GET** `/cards/`: Retrieve all cards
- **GET** `/cards/<hash>`: Get specific card
- **POST** `/cards/`: Create new card
- **DELETE** `/cards/<hash>`: Delete card
- **GET** `/search`: Search cards with pagination

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
    ├── multi_card_container.html         # Main container with controls
    ├── card_list.html                    # Card grid with pagination
    ├── single_card_container.html        # Detail view
    └── macros/
        ├── pagination.html               # Pagination component
        └── card_content_display.html     # Content rendering
```

## Recent Updates

1. **Component Reorganization**
   - Separated card list from container for better reusability
   - Integrated pagination directly into card list component
   - Improved search bar implementation with debouncing
   - Enhanced grid column controls

2. **Pagination Improvements**
   - Moved pagination controls into card list component
   - Improved pagination state management during search
   - Added support for maintaining state across operations

3. **UI Enhancements**
   - Improved search responsiveness with debouncing
   - Enhanced grid column controls
   - Better error handling and user feedback
   - Cleaner component separation and styling

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
