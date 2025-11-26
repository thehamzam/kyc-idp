# Document Extraction

A web application that uses Fireworks AI to extract personal information from uploaded images of licenses and passports.

## Features

- Upload images of licenses or passports
- AI-powered extraction of personal information (name, DOB, document number, etc.)
- Side-by-side view of uploaded image and extracted data
- Support for multiple document uploads in a session

## Prerequisites

- Python 3.9 or higher
- A Fireworks AI API key ([Get one here](https://fireworks.ai/))

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your API key:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and replace `your_api_key_here` with your actual Fireworks AI API key:
   ```
   FIREWORKS_API_KEY=your_actual_api_key
   ```

## Running the Application

Start the server:
```bash
python app.py
```

The application will start on **http://localhost:5000**

## Usage

1. Open http://localhost:5000 in your browser
2. Click the upload area or drag and drop an image of a license or passport
3. Click "Extract Information" to process the document
4. View the extracted information alongside the uploaded image
5. Click "Upload Another Document" to process additional documents

## Supported File Types

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

Maximum file size: 10MB

## Configuration

Environment variables (set in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `FIREWORKS_API_KEY` | Your Fireworks AI API key | (required) |
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_PORT` | Port to run the server | `5000` |
| `MAX_FILE_SIZE_MB` | Maximum upload file size | `10` |
| `ALLOWED_EXTENSIONS` | Allowed file extensions | `jpg,jpeg,png,gif` |

## Troubleshooting

### "API configuration error" message
- Ensure your `FIREWORKS_API_KEY` is set correctly in the `.env` file
- Verify your API key is valid at https://fireworks.ai/

### "File size exceeds maximum limit"
- The default limit is 10MB. Reduce your image size or adjust `MAX_FILE_SIZE_MB` in `.env`

### "Invalid file type" error
- Ensure you're uploading a supported image format (JPEG, PNG, GIF, WebP)

### No information extracted
- Ensure the document image is clear and well-lit
- Make sure the entire document is visible in the image
- Try a higher resolution image

## Project Structure

```
├── app.py                 # Flask application
├── models.py              # Data models and validation
├── fireworks_client.py    # Fireworks AI integration
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── static/
│   ├── app.js            # Frontend JavaScript
│   └── style.css         # Styles
└── templates/
    └── index.html        # Main HTML template
```

