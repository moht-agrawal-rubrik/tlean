# Backend API

A FastAPI-based backend service providing REST API endpoints.

## Prerequisites

Before setting up the backend locally, ensure you have the following installed:

- **Python 3.12+** - Required for running the application
- **uv** - Modern Python package manager (recommended) or pip as fallback

### Installing uv (Recommended)

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Install via pip
pip install uv
```

## Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tlean/backend
```

### 2. Create Virtual Environment and Install Dependencies

Using uv (recommended):
```bash
# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

Alternative using pip:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt  # If requirements.txt exists
# or install from pyproject.toml
pip install -e .
```

## Running the Application

### Development Server

Start the development server with hot reload:

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the FastAPI CLI (if available)
fastapi dev main.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Interactive API Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative API Documentation (ReDoc)**: http://localhost:8000/redoc

### Production Server

For production deployment:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

The backend currently provides the following endpoints:

- `GET /` - Root endpoint returning a welcome message
- `GET /hello/{name}` - Personalized greeting endpoint
- `GET /health` - Health check endpoint for monitoring

### Example API Calls

```bash
# Root endpoint
curl http://localhost:8000/

# Hello endpoint
curl http://localhost:8000/hello/world

# Health check
curl http://localhost:8000/health
```

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── README.md           # This file
└── .venv/              # Virtual environment (created after setup)
```

### Adding Dependencies

Using uv:
```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name
```

Using pip:
```bash
# Install and add to requirements
pip install package-name
pip freeze > requirements.txt
```

### Environment Variables

The application supports environment variables for configuration. Create a `.env` file in the backend directory:

```bash
# .env file example
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## Troubleshooting

### Common Issues

1. **Python version mismatch**: Ensure you're using Python 3.12+
   ```bash
   python --version
   ```

2. **Virtual environment not activated**: Make sure to activate the virtual environment
   ```bash
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

3. **Port already in use**: If port 8000 is busy, use a different port
   ```bash
   uvicorn main:app --reload --port 8001
   ```

4. **Dependencies not installed**: Reinstall dependencies
   ```bash
   uv sync  # or pip install -e .
   ```

### Getting Help

- Check the FastAPI documentation: https://fastapi.tiangolo.com/
- Review the uvicorn documentation: https://www.uvicorn.org/
- For uv package manager: https://docs.astral.sh/uv/

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes locally
5. Submit a pull request

## License

[Add your license information here]