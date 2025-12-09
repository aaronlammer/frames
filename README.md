# Vibecode - Claude Opus 4.5 Web Application

A modern web application for interacting with Claude Opus 4.5 via the Anthropic API. Features a beautiful, responsive web interface built with FastAPI and vanilla JavaScript.

## Features

- 🌐 Modern web interface with real-time chat
- 🚀 Fast FastAPI backend with async support
- 🎨 Beautiful, responsive UI with dark theme
- 💬 Interactive chat interface
- 📱 Mobile-friendly design
- 🔄 Auto-reload in development mode

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
cp env.template .env
```

Then edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your-actual-api-key-here
```

You can get your API key from the [Anthropic Console](https://console.anthropic.com/account/keys).

## Running the Web Application

### Development Mode (with auto-reload)

```bash
python run.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The webapp will be available at: **http://localhost:8000**

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
vibecode/
├── app/                    # Backend application
│   ├── __init__.py
│   ├── main.py            # FastAPI app entry point
│   ├── api/               # API routes
│   │   ├── __init__.py
│   │   └── chat.py        # Chat API endpoint
│   └── services/          # Business logic
│       ├── __init__.py
│       └── claude_service.py  # Claude API integration
├── static/                # Frontend files
│   ├── index.html         # Main HTML page
│   ├── styles.css         # Styling
│   └── app.js             # Frontend JavaScript
├── run.py                 # Development server script
├── requirements.txt       # Python dependencies
├── env.template          # Environment variable template
├── .env                  # Your API key (create from template)
├── test_claude.py        # CLI test script
└── example.py            # CLI example script
```

## Usage

### Web Application

1. Start the server: `python run.py`
2. Open your browser to `http://localhost:8000`
3. Start chatting with Claude Opus!

### CLI Tools (Still Available)

#### Test Script

Send a test message to Claude Opus 4.5:

```bash
python test_claude.py
```

With a custom message:

```bash
python test_claude.py "Your custom message here"
```

#### Example Script

Run the interactive example:

```bash
python example.py
```

This will prompt you for a message and display Claude's response.

## API Endpoints

### POST `/api/chat/`

Send a message to Claude and get a response.

**Request:**
```json
{
  "message": "Your message here",
  "model": "claude-opus-4-5-20251101"  // optional
}
```

**Response:**
```json
{
  "response": "Claude's response text"
}
```

## Model Support

The application automatically tries different Opus model identifiers:
- `claude-opus-4-5-20251101` (Opus 4.5)
- `claude-opus-4-20250514` (Opus 4)
- `claude-3-opus-20240229` (Opus 3, fallback)

## Development

### Running in Development Mode

The `run.py` script includes auto-reload for development. Any changes to Python files will automatically restart the server.

### Frontend Development

Static files are served from the `static/` directory. Changes to HTML, CSS, or JavaScript files will be immediately visible after a browser refresh.

## Notes

- Make sure your Anthropic account has sufficient credits to use Opus models
- The `.env` file is gitignored for security
- Error messages will indicate if the API key is missing or invalid
- For production, configure CORS properly in `app/main.py` to restrict origins

## License

MIT
