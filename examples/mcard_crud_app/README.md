# MCard CRUD App

A simple CRUD (Create, Read, Update, Delete) application built with Flask and MCard for storing and managing content. This application demonstrates the basic usage of the MCard library for content storage and retrieval.

## Features

- Create new cards with text content or file uploads
- View all cards in a grid layout
- View individual card details
- Delete cards
- Support for various content types:
  - Plain text
  - JSON
  - Binary files (with special handling for images)
- Drag and drop file upload support
- Duplicate content detection
- Responsive design with Bootstrap 5

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required packages:
   ```bash
   pip install flask mcard
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

### Creating Cards

1. Click the "New Card" button in the navigation bar or on the home page
2. Choose between:
   - Text content: Enter text directly in the textarea
   - File upload: Select a file or drag and drop it into the upload area

### Viewing Cards

- The home page displays all cards in a grid layout
- Click the "View" button on a card to see its full details
- Binary files (like images) can be previewed and downloaded

### Deleting Cards

- Use the "Delete" button on either the card grid or the view page
- Confirm the deletion when prompted

## Project Structure

```
mcard_crud_app/
├── app.py              # Main application file
├── templates/          # HTML templates
│   ├── base.html      # Base template with common layout
│   ├── index.html     # Home page template
│   ├── new_card.html  # New card creation template
│   └── view_card.html # Card detail view template
└── README.md          # This file
```

## Contributing

Feel free to submit issues and enhancement requests!
