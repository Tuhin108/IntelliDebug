# 🤖 IntelliDebug

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-lightgrey.svg)](https://flask.palletsprojects.com/)

A powerful web-based Python debugger with AI-powered error explanations and fix suggestions using Google's Gemini AI. Execute Python code safely in a sandboxed environment and get intelligent debugging assistance.

## ✨ Features

- **🔒 Safe Code Execution**: Sandboxed Python code execution with timeout protection
- **🤖 AI-Powered Analysis**: Intelligent error explanations using Google Gemini AI
- **🔍 Syntax Validation**: Real-time syntax error detection before execution
- **⚡ Runtime Debugging**: Comprehensive runtime error analysis and handling
- **🌐 Modern Web Interface**: Beautiful, responsive UI with syntax highlighting
- **📊 Real-time Results**: Instant feedback with AI-powered suggestions
- **💡 Educational Focus**: Student-friendly explanations and learning approach

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key (for AI features)

### Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd IntelliDebug
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   Create a `.env` file:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://127.0.0.1:5000` to start debugging!

## 📖 Usage

### Web Interface
- Navigate to the web interface in your browser
- Enter Python code in the editor
- Click "Run Code" to execute and get AI analysis
- View detailed explanations and suggested fixes

### API Usage

**Debug Endpoint** (`POST /debug`)
```bash
curl -X POST http://localhost:5000/debug \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")"}'
```

**Response:**
```json
{
  "success": true,
  "output": "Hello, World!",
  "error": null,
  "ai_explanation": "Code executed successfully! 🎉"
}
```

**Health Check** (`GET /health`)
```bash
curl http://localhost:5000/health
```

## 🛡️ Security Features

- **Sandboxed Execution**: Code runs in isolated subprocesses
- **Timeout Protection**: 5-second execution limit prevents hanging
- **Output Limits**: Prevents memory exhaustion from large outputs
- **Input Validation**: Comprehensive request validation
- **Error Sanitization**: Safe error message handling

## ⚙️ Configuration

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required for AI features)
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: True)

### Optional Settings
- `MAX_EXECUTION_TIME`: Code execution timeout in seconds (default: 5)
- `MAX_OUTPUT_LENGTH`: Maximum output length (default: 2000)

## 🔧 Development

### Project Structure
```
IntelliDebug/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
├── .env               # Environment variables
├── .gitignore        # Git ignore rules
└── templates/
    └── index.html    # Web interface
```

### Local Development
```bash
# Enable debug mode
export FLASK_DEBUG=True
python app.py

# Use custom port
export PORT=8000
python app.py
```

## 🐛 Troubleshooting

### Common Issues

**AI features not working**
- Verify `GEMINI_API_KEY` is set correctly
- Check API key permissions in Google AI Studio
- Ensure stable internet connection

**Code execution timeout**
- Code execution limited to 5 seconds by default
- Check for infinite loops in your code
- Consider optimizing long-running algorithms

**Port already in use**
```bash
# Use different port
export PORT=8000
python app.py

# Or kill existing process
lsof -ti:5000 | xargs kill -9
```

### Debug Information
Check `debugger.log` for detailed error information and troubleshooting data.

## 📊 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/debug` | Execute Python code and get analysis |
| `GET` | `/health` | Health check and service status |
| `GET` | `/` | Web interface |

### Debug Request Format
```json
{
  "code": "your_python_code_here"
}
```

### Debug Response Format
```json
{
  "success": boolean,
  "output": string,
  "error": string|null,
  "error_type": "syntax"|"runtime"|null,
  "ai_explanation": string,
  "suggested_fix": string|null,
  "fix_explanation": string|null
}
```
## 📷 Screenshot
<img width="1919" height="971" alt="image" src="https://github.com/user-attachments/assets/2879c470-ab73-424b-b6a8-f8cd081bf519" />


---

**Made with ❤️ by Tuhin for Python learners**

For more information, visit our [GitHub repository](https://github.com/Tuhin108/IntelliDebug).
