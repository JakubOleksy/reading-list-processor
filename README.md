# Reading List Processor

A web application that extracts URLs from your Safari Reading List and uses Claude AI to generate summaries of the articles.

## Features

- **Safari Integration**: Automatically syncs URLs from your Safari Reading List
- **AI Summarization**: Uses Claude API to generate intelligent summaries
- **Custom Instructions**: Add your own instructions to customize how articles are summarized
- **Flexible Processing**: Process individual items or batch process multiple items
- **Reprocessing Options**: Choose to reprocess all items or only new ones
- **Clean UI**: Simple, modern interface to view and manage your reading list

## Tech Stack

- **Backend**: Python + FastAPI
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript
- **AI**: Anthropic Claude API
- **Web Scraping**: BeautifulSoup + Requests

## Setup Instructions

### 1. Clone the Repository

```bash
cd /Users/jakuboleksy/github/reading-list-processor
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
SAFARI_BOOKMARKS_PATH=/Users/yourusername/Library/Safari/Bookmarks.plist
```

Replace `your_actual_api_key_here` with your Anthropic API key.

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

## Usage

1. **Sync Reading List**: Click "Sync from Safari" to import URLs from your Safari Reading List
2. **View Items**: All imported items will be displayed with their title, URL, and preview text
3. **Process Items**:
   - Click "Process" on individual items to generate a summary
   - Click "Process All Unprocessed" to process all items that haven't been summarized yet
   - Click "Reprocess All" to regenerate summaries for all items
4. **Custom Instructions**: Click "Settings" to add custom instructions for how Claude should summarize articles
5. **Delete Items**: Remove items from the database by clicking "Delete"

## API Endpoints

- `GET /` - Main web interface
- `GET /api/items` - Get all reading list items
- `POST /api/sync` - Sync from Safari Reading List
- `POST /api/process` - Process items with Claude
- `GET /api/settings` - Get application settings
- `POST /api/settings` - Update application settings
- `DELETE /api/items/{item_id}` - Delete an item

## Project Structure

```
reading-list-processor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── database.py          # Database configuration
│   ├── safari_reader.py     # Safari Reading List parser
│   ├── summarizer.py        # Claude API integration
│   ├── static/
│   │   ├── styles.css       # Styles
│   │   └── app.js           # Frontend JavaScript
│   └── templates/
│       └── index.html       # Main HTML template
├── requirements.txt
├── .env
└── README.md
```

## Notes

- The application reads your Safari Reading List from the Bookmarks.plist file (read-only)
- All data is stored in a local SQLite database (`reading_list.db`)
- The Claude API requires an active Anthropic account and API key
- Processing times depend on article length and API response times
