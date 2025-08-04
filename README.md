# FastBoard - Real-time Collaborative Whiteboard

A modern, real-time collaborative whiteboard application built with FastAPI, WebSockets, and AI-powered canvas interpretation.

## ✨ Features

- **Real-time Collaboration**: Multiple users can draw simultaneously with live cursor tracking
- **AI Canvas Interpretation**: Powered by OpenAI's GPT-4 Vision to convert drawings into structured formats
- **Responsive Design**: Works seamlessly across desktop and mobile devices
- **Professional Architecture**: Modular, scalable, and maintainable codebase
- **Type Safety**: Full type hints and Pydantic models for data validation
- **Comprehensive Logging**: Structured logging with multiple levels and outputs
- **Rate Limiting**: Built-in protection against API abuse
- **Health Monitoring**: Health check endpoints for monitoring and alerting

## 🏗️ Architecture

FastBoard follows enterprise-grade software architecture principles:

```
app/
├── core/                  # Core functionality
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exception classes
│   └── logging.py        # Logging configuration
├── models/               # Data models
│   └── schemas.py        # Pydantic models for validation
├── services/             # Business logic layer
│   ├── ai_service.py     # OpenAI integration
│   └── connection_manager.py  # WebSocket management
├── api/                  # API endpoints
│   ├── endpoints.py      # REST API routes
│   └── websocket.py      # WebSocket handlers
├── utils/                # Utility functions
│   └── helpers.py        # Common helper functions
└── main.py               # Application factory
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (optional, for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fast-board
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Unix/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   copy .env.example .env
   # Edit .env with your settings, especially OPENAI_API_KEY
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

## 🔧 Configuration

FastBoard uses environment variables for configuration. Key settings include:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | None | OpenAI API key for AI features |
| `DEBUG` | True | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |
| `LOG_LEVEL` | INFO | Logging level |
| `MAX_CANVAS_SIZE` | 4096 | Maximum canvas dimension |
| `RATE_LIMIT_REQUESTS` | 100 | AI requests per minute |

See `.env.example` for all available settings.

## 🔌 API Documentation

### REST Endpoints

- `GET /` - Main application interface
- `POST /api/v1/ai-assist` - AI canvas interpretation
- `GET /api/v1/health` - Health check
- `GET /api/v1/info` - Application information

### WebSocket Endpoints

- `WS /ws/{client_id}` - Real-time collaboration
- `GET /ws/stats` - WebSocket statistics

Interactive API documentation available at `/docs` (debug mode only).

## 🧠 AI Features

FastBoard integrates with OpenAI's GPT-4 Vision model to provide intelligent canvas interpretation:

- **Diagram Recognition**: Converts flowcharts to Mermaid.js code
- **Note Organization**: Transforms sketches into structured Markdown
- **Mathematical Expressions**: Recognizes and formats equations
- **Smart Descriptions**: Provides meaningful descriptions of complex drawings

### Using AI Features

1. Draw or write on the canvas
2. Click the "AI Assist" button
3. The AI will analyze your drawing and provide structured output
4. Copy the result for use in other applications

## 🏆 Best Practices Implemented

### Code Quality
- **Separation of Concerns**: Clear separation between API, business logic, and data layers
- **Dependency Injection**: Proper dependency management with FastAPI's DI system
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Error Handling**: Custom exceptions with specific error codes
- **Input Validation**: Pydantic models for all data validation

### Security
- **Rate Limiting**: Protection against API abuse
- **Input Sanitization**: Safe handling of user input
- **CORS Configuration**: Proper cross-origin request handling
- **Trusted Host Middleware**: Protection against host header attacks

### Performance
- **Async/Await**: Full asynchronous support for scalability
- **Connection Pooling**: Efficient WebSocket connection management
- **Memory Management**: Automatic cleanup of inactive connections
- **Resource Limits**: Configurable limits for canvas size and stroke points

### Monitoring
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Health Checks**: Comprehensive health monitoring endpoints
- **Metrics Collection**: Built-in connection and performance metrics
- **Error Tracking**: Detailed error logging with stack traces

## 🧪 Development

### Running in Development Mode

```bash
# Enable debug mode in .env
DEBUG=True

# Run with auto-reload
python main.py
```

### Code Style

The project follows PEP 8 and uses:
- Type hints for all functions
- Docstrings for all classes and methods
- Descriptive variable and function names
- Consistent error handling patterns

### Testing Structure

The modular architecture makes testing straightforward:

```python
# Example test structure
tests/
├── test_api/
├── test_services/
├── test_models/
└── conftest.py
```

## 🚀 Deployment

### Production Configuration

1. **Set production environment variables**
   ```bash
   DEBUG=False
   LOG_LEVEL=WARNING
   ```

2. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Configure reverse proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /ws/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style and patterns
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- OpenAI for AI capabilities
- The open-source community for inspiration and tools

---

Built with ❤️ by senior developers following industry best practices.
