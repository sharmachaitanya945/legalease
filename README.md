# LegalEase AI

<div align="center">
  <img src="static/logo.png" alt="LegalEase AI Logo" width="200">
</div>

![legalease](https://socialify.git.ci/sharmachaitanya945/legalease/image?custom_description=LegalEase+AI+-+Intelligent+Legal+Research+Platform*&description=1&language=1&name=1&owner=1&pattern=Brick+Wall&stargazers=1&theme=Dark)

A comprehensive legal research web application powered by MindsDB, Ollama, and Gemini AI. This application provides intelligent legal document search, semantic understanding, and AI-powered legal assistance.

## 📺 Demo & Documentation

### 🎥 Video Walkthrough
📹 **YouTube Demo**: *Coming Soon!* - Complete application walkthrough and setup guide

### 📝 Blog Posts
📖 **Medium.com**: *Coming Soon!* - Deep dive into MindsDB Knowledge Base integration  
📖 **Dev.to**: *Coming Soon!* - Building AI-powered legal research with semantic search

### 📋 Project Documentation
📄 **[SUBMISSION.md](SUBMISSION.md)** - Complete rubric compliance mapping and implementation details

## Features

🔍 **Semantic Search**: Search through legal documents using natural language queries
🤖 **AI Legal Assistant**: Get intelligent answers powered by Gemini 2.0 Flash
📁 **Document Upload**: Easily upload CSV files to expand the knowledge base
🏷️ **Smart Filtering**: Filter results by category, relevance, and metadata
⚡ **Real-time Processing**: Fast document processing with PGVector storage
🔄 **Retry Mechanisms**: Robust error handling and automatic retries
📋 **Job Management**: Schedule automated tasks for data ingestion and maintenance

## Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: 
  - Ollama (mxbai-embed-large for embeddings) - Auto-downloaded via Docker
  - Gemini 2.0 Flash (for reranking and AI responses)
- **Vector Database**: PostgreSQL with pgvector extension for CREATE INDEX operations
- **Database**: MindsDB with PostgreSQL pgvector storage backend
- **Containerization**: Docker Compose with 5 services:
  - `postgres`: PostgreSQL 16 with pgvector extension
  - `mindsdb`: MindsDB server (latest)
  - `ollama`: Ollama server with mxbai-embed-large model
  - `ollama-puller`: Automatic model downloader
  - `legalease-app`: Main Flask web application
- **Frontend**: Bootstrap 5 with custom CSS
- **Knowledge Base**: MindsDB Knowledge Base with semantic search via pgvector indexing

## Prerequisites

1. **MindsDB Server** running on `http://127.0.0.1:47334`
2. **Ollama** running on `http://localhost:11434` with `mxbai-embed-large` model
3. **PostgreSQL with pgvector extension** (Docker container recommended)
4. **Python 3.8+**

**Note**: This application uses PostgreSQL with pgvector extension for vector storage and CREATE INDEX operations, not ChromaDB.

## 🐳 Quick Start with Docker (Recommended)

The easiest way to run LegalEase AI is using Docker Compose, which sets up all required services automatically:

### Prerequisites for Docker Setup
- Docker and Docker Compose installed
- Google API key for Gemini model

### Docker Installation Steps

1. **Clone the repository**:
```bash
git clone https://github.com/sharmachaitanya945/legalease.git
cd legalease
```

2. **Set up environment variables**:
```bash
cp .env.docker .env
```

3. **Configure your Google API key** in `.env`:
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
```

4. **Start all services** (this will download and set up everything):
```bash
docker-compose up -d
```

This single command will:
- ✅ Download and start PostgreSQL with pgvector extension
- ✅ Download and start MindsDB server
- ✅ Download and start Ollama with mxbai-embed-large model
- ✅ Build and start the LegalEase AI web application

5. **Access the application**:
   - Web Interface: `http://localhost:5000`
   - MindsDB: `http://localhost:47334`
   - Ollama API: `http://localhost:11434`

6. **Initialize the system**: Visit the homepage and click "Initialize System"

### 🛠️ Docker Management Commands

#### Using the Setup Scripts (Recommended)
```bash
# Linux/Mac
./docker-setup.sh start    # Start all services
./docker-setup.sh stop     # Stop all services
./docker-setup.sh logs     # View logs
./docker-setup.sh status   # Check service status
./docker-setup.sh reset    # Reset all data

# Windows
docker-setup.bat start     # Start all services
docker-setup.bat stop      # Stop all services
docker-setup.bat logs      # View logs
docker-setup.bat status    # Check service status
docker-setup.bat reset     # Reset all data
```

#### Manual Docker Commands
```bash
# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# Remove all data and start fresh
docker-compose down -v
docker-compose up -d
```

## 📋 Manual Installation (Alternative)

If you prefer to install services manually instead of using Docker:

### Prerequisites for Manual Setup
1. **MindsDB Server** running on `http://127.0.0.1:47334`
2. **Ollama** running on `http://localhost:11434` with `mxbai-embed-large` model
3. **PostgreSQL with pgvector extension**
4. **Python 3.8+**

### Manual Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/legalease.git
cd legalease
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Configure your `.env` file with your actual values:
```env
# MindsDB Configuration
MINDSDB_HOST=127.0.0.1
MINDSDB_PORT=47334
MINDSDB_DATABASE=legalease

# Google AI API (Required)
GOOGLE_API_KEY=your_actual_google_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here_min_32_characters_long
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=legal_vector_db
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password

# Security
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
```

## 🔒 Security & Configuration

⚠️ **Important Security Notes**:

1. **Never commit sensitive data** like API keys or passwords to version control
2. **Always use environment variables** for configuration
3. **Use strong secret keys** (minimum 32 characters)
4. **Keep your `.env` file private** - it's already in `.gitignore`
5. **Validate all uploaded files** before processing
6. **Use HTTPS in production**

### Environment Variables Setup

Copy the `.env.example` file to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

**Required Variables**:
- `GOOGLE_API_KEY`: Your Google AI API key for Gemini model
- `FLASK_SECRET_KEY`: A secure random string (32+ characters)

**Optional Variables** (have defaults):
- `MINDSDB_HOST`, `MINDSDB_PORT`: MindsDB connection details
- `OLLAMA_BASE_URL`: Ollama server URL
- `POSTGRES_*`: PostgreSQL configuration

## Usage

1. **Start the application**:
```bash
python app.py
```

2. **Access the web interface**:
   - Open your browser to `http://localhost:5000`

3. **Initialize the system**:
   - Click "Initialize System" on the homepage to set up the knowledge base and AI agent

4. **Upload documents**:
   - Go to the Upload page
   - Upload a CSV file with columns: `doc_id`, `title`, `category`, `content`

5. **Search documents**:
   - Use the Search page for semantic document search
   - Filter by category and adjust result limits

6. **Ask the AI Assistant**:
   - Use the AI Assistant page for natural language legal questions
   - Get comprehensive answers with relevant case citations

## API Endpoints

- `POST /api/search` - Perform semantic search
- `POST /api/agent` - Query the AI assistant
- `POST /api/upload` - Upload CSV documents
- `POST /api/initialize` - Initialize knowledge base and agent
- `GET /api/status` - Check system status
- `GET /api/categories` - Get available categories

## CSV File Format

Your CSV files must include these columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `doc_id` | Integer | Unique document ID | 1, 2, 3... |
| `title` | String | Document title | "Miranda v. Arizona" |
| `category` | String | Legal category | "Criminal Law" |
| `content` | String | Document content | "The Supreme Court held..." |

## Configuration

The application uses the following default configurations:

- **MindsDB**: `http://127.0.0.1:47334`
- **Ollama**: `http://localhost:11434`
- **Vector Storage**: PostgreSQL with pgvector extension (not ChromaDB)
- **Embedding Model**: `mxbai-embed-large`
- **AI Model**: `gemini-2.0-flash`
- **Max File Size**: 16MB
- **Index Type**: PostgreSQL pgvector indexes via `CREATE INDEX ON KNOWLEDGE_BASE`

## Error Handling

The application includes comprehensive error handling:

- Automatic retries for connection issues
- Graceful handling of litellm errors
- User-friendly error messages
- Robust file upload validation

## Development

To run in development mode:

```bash
export FLASK_ENV=development
python app.py
```

## Production Deployment

For production deployment:

1. Use a production WSGI server like Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. Configure environment variables for security
3. Set up proper logging and monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

**Made with ❤️ by [sharmachaitanya945](https://github.com/sharmachaitanya945)**

Powered by:
- [MindsDB](https://mindsdb.com/) - AI database platform
- [Ollama](https://ollama.ai/) - Local LLM runner
- [Google Gemini](https://gemini.google.com/) - Advanced AI model

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

---

*LegalEase AI - Intelligent Legal Research Platform*

## Jobs Management

LegalEase AI includes a comprehensive job management system for automating tasks and data processing.

### Available Job Types

1. **CSV Data Ingestion**: Automatically ingest new documents from uploaded files
2. **Knowledge Base Maintenance**: Rebuild indexes and optimize performance 
3. **Index Rebuild**: Recreate search indexes for better performance
4. **Custom Queries**: Run your own MindsDB queries on schedule

### Creating Jobs

#### CSV Auto-Ingestion Job
```sql
CREATE JOB ingest_from_csv
AS (
  INSERT INTO legal_kb_pg
  SELECT
    doc_id,
    title,
    category,
    content
  FROM files.legal_docs
  WHERE doc_id > LAST;
)
EVERY 1 HOUR;
```

#### Knowledge Base Maintenance Job
```sql
CREATE JOB kb_maintenance
AS (
  CREATE INDEX ON KNOWLEDGE_BASE legalease.legal_kb_pg;
)
EVERY 1 DAY;
```

**Note**: The `CREATE INDEX` operation uses PostgreSQL with pgvector extension for optimal vector similarity search performance, not ChromaDB indexing.

### Managing Jobs

```sql
-- List all active jobs
SHOW JOBS;

-- Stop/delete a job
DROP JOB ingest_from_csv;

-- Check job status
SELECT * FROM information_schema.jobs 
WHERE name = 'ingest_from_csv';
```

### Using the Jobs Interface

1. **Navigate to Jobs**: Click "Jobs" in the navigation menu
2. **Create New Job**: Fill out the form with job details
3. **Use Templates**: Click template buttons for quick job creation
4. **Monitor Jobs**: View active jobs in the dashboard
5. **Stop Jobs**: Use the stop button to halt running jobs

### Job Features

- **Automated Execution**: Jobs run automatically on specified schedules
- **Incremental Processing**: Only processes new data using the `LAST` keyword
- **Error Handling**: Built-in retry mechanisms for failed executions  
- **Monitoring**: Track job status, execution history, and performance
- **Transparency**: View actual MindsDB queries being executed

### Testing Jobs

Run the test script to verify job functionality:

```bash
python test_jobs.py
```

This will test job creation, listing, and deletion through the API.

## Contributing
