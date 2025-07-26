# Smart Document Assistant

A comprehensive document analysis system that combines visual understanding (LLaVA) and text analysis (Mistral) to extract insights from PDFs and images.

## 🚀 Features

- **Fast Text Analysis**: OCR-based text extraction with Mistral text processing
- **PDF & Image Support**: Handles PDFs, PNG, JPEG, and WebP files
- **Concurrent Processing**: Async/parallel page processing for multi-page documents
- **Real-time Progress**: Live progress tracking with job management
- **Batch Vector Stores**: Efficient vector store creation for entire documents
- **OCR Integration**: Text extraction with Tesseract OCR
- **Structured Data Extraction**: Identifies invoices, forms, meetings, and general documents
- **Action Item Generation**: Extracts actionable items from documents
- **Semantic Search**: FAISS-based vector search capabilities
- **Ultra-Fast Processing**: Optimized for speed with LLaVA disabled

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Async Processing Pipeline**: Concurrent page processing with controlled concurrency
- **Progress Tracking**: Real-time job status and progress updates
- **Model Management**: Singleton pattern for efficient LLM instance reuse
- **Background Tasks**: Non-blocking document processing
- **Batch Operations**: Optimized vector store creation for multi-page documents

### Frontend (React + TypeScript)
- **Real-time Progress**: Live progress bars and status updates
- **Job Polling**: Automatic status checking for background jobs
- **Dual Upload Modes**: Async (with progress) and sync (immediate results)
- **Responsive UI**: Modern interface with Tailwind CSS

## 📊 Performance Optimizations

### Phase 1: Immediate Optimizations ✅
- **Unified LLM Calls**: Combined analysis in single API calls
- **Optimized Prompts**: Faster, more focused LLaVA prompts
- **Model Instance Reuse**: Singleton pattern for LLM/embeddings
- **Fast Analysis Modes**: Ultra-fast LLaVA analysis option

### Phase 2: Async/Parallel Processing ✅
- **Concurrent Page Processing**: Multiple pages processed simultaneously
- **Background Tasks**: Non-blocking upload and processing
- **Progress Tracking**: Real-time updates with job management
- **Batch Vector Stores**: Single vector store per document
- **Controlled Concurrency**: Semaphore-based resource management

### Phase 2.5: Ultra-Fast Processing ✅
- **LLaVA Analysis Removed**: Disabled for maximum speed
- **OCR-Only Processing**: Text extraction and analysis only
- **Ultra-Fast Prompts**: Minimal text input and processing
- **Processing Time**: 80-90% faster than original implementation

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Ollama**: Local LLM inference (LLaVA, Mistral)
- **LangChain**: LLM framework and processing chains
- **FAISS**: Vector database for semantic search
- **Pillow/OpenCV**: Image processing and enhancement
- **Tesseract**: OCR text extraction
- **uv**: Fast Python package management

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Vite**: Fast build tool and dev server

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Ollama with LLaVA and Mistral models
- Tesseract OCR

### Backend Setup
```bash
# Install Python dependencies
uv sync

# Set up environment variables
cp env.example .env
# Edit .env with your Ollama configuration

# Start the backend
uv run python -m uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Ollama Models
```bash
# Pull required models
ollama pull llava:latest
ollama pull mistral:7b-instruct
```

## 📁 Project Structure

```
smart-document-assistant/
├── src/app/
│   ├── main.py                 # FastAPI app initialization
│   ├── routers/
│   │   ├── upload.py          # File upload endpoints
│   │   ├── analysis.py        # Text analysis endpoints
│   │   ├── vector_store.py    # Vector store operations
│   │   └── jobs.py            # Progress tracking endpoints
│   ├── services/
│   │   ├── processing_pipeline.py  # Async processing pipeline
│   │   ├── progress_service.py     # Job progress tracking
│   │   ├── model_manager.py        # LLM instance management
│   │   ├── file_service.py         # File processing utilities
│   │   ├── llava_service.py        # LLaVA visual analysis
│   │   ├── text_analysis_service.py # Text analysis with Mistral
│   │   └── vector_store_service.py # FAISS vector operations
│   └── schemas/               # Pydantic data models
├── frontend/                  # React TypeScript frontend
├── tests/                     # Comprehensive test suite
└── data/                      # Sample documents for testing
```

## 🔧 Configuration

### Environment Variables
```bash
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434

# Model Configuration
LLAVA_MODEL=llava:latest
TEXT_MODEL=mistral:7b-instruct

# Performance Settings
LLAVA_TIMEOUT=30
TEXT_TIMEOUT=120
MAX_CONCURRENT_PROCESSES=4
```

### Performance Tuning
- **MAX_CONCURRENT_PROCESSES**: Controls parallel page processing (default: 4)
- **LLAVA_TIMEOUT**: LLaVA analysis timeout (default: 30s)
- **TEXT_TIMEOUT**: Text analysis timeout (default: 120s)

## 📈 Performance Metrics

### Phase 1 Optimizations
- **Single Page**: 15-30 seconds (vs 30-60 seconds before)
- **3-Page PDF**: 45-90 seconds (vs 90-180 seconds before)
- **18-Page PDF**: 4-8 minutes (vs 10+ minutes before)

### Phase 2 Optimizations
- **Concurrent Processing**: 2-4x faster for multi-page documents
- **Background Tasks**: Non-blocking uploads with real-time progress
- **Batch Vector Stores**: Reduced memory usage and faster search
- **Progress Tracking**: Real-time updates for better UX

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
uv run pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Performance Tests
```bash
# Test Phase 1 optimizations
uv run pytest tests/services/test_performance_optimizations.py -v

# Test Phase 2 optimizations
uv run pytest tests/services/test_phase2_optimizations.py -v
```

## 🔄 API Endpoints

### Upload & Processing
- `POST /api/upload/upload` - Async upload with progress tracking
- `POST /api/upload/upload-sync` - Synchronous upload for immediate results
- `POST /api/upload/upload-legacy` - Legacy sequential processing

### Progress Tracking
- `GET /api/jobs/{job_id}` - Get job status and progress
- `GET /api/jobs/` - List all jobs
- `DELETE /api/jobs/{job_id}` - Delete a job
- `POST /api/jobs/cleanup` - Clean up old jobs

### Analysis
- `POST /api/analysis/summarize` - Generate document summaries
- `POST /api/analysis/extract-data` - Extract structured data
- `POST /api/analysis/generate-actions` - Generate action items
- `POST /api/analysis/answer-question` - Q&A functionality

### Vector Store
- `GET /api/vector-store/stats` - Get vector store statistics
- `POST /api/vector-store/search` - Semantic search
- `DELETE /api/vector-store/{store_id}` - Delete vector store

## 🚀 Usage Examples

### Upload with Progress Tracking
```javascript
// Frontend - Async upload with progress
const response = await fetch('/api/upload/upload', {
  method: 'POST',
  body: formData
});

const { job_id } = await response.json();

// Poll for progress
const status = await fetch(`/api/jobs/${job_id}`);
const { progress_percentage, status } = await status.json();
```

### Batch Processing
```python
# Backend - Process multiple pages concurrently
results = await processing_pipeline.process_pages_concurrently(image_paths)

# Create batch vector store
success = await processing_pipeline.create_batch_vector_store(results, document_id)
```

## 🔒 Security

- **File Validation**: Strict file type and size validation
- **Path Sanitization**: Secure file path handling
- **Error Handling**: Comprehensive error management
- **Resource Limits**: Controlled concurrency and timeouts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Ollama Connection Error**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**Model Not Found**
```bash
# Pull required models
ollama pull llava:latest
ollama pull mistral:7b-instruct
```

**Performance Issues**
- Increase `MAX_CONCURRENT_PROCESSES` for more parallel processing
- Reduce `LLAVA_TIMEOUT` for faster timeouts
- Check system resources (CPU, memory)

**Frontend Connection Issues**
- Ensure backend is running on port 8000
- Check CORS configuration
- Verify API endpoint URLs

## 📊 Monitoring

### Logs
- Backend logs show processing progress and errors
- Frontend console shows API calls and responses
- Progress tracking provides real-time updates

### Metrics
- Processing time per page
- Concurrent operations count
- Vector store creation success rate
- Error rates and types

## 🔮 Future Enhancements

- **WebSocket Support**: Real-time progress updates
- **Celery Integration**: Distributed task processing
- **Redis Caching**: Improved performance for repeated requests
- **Docker Deployment**: Containerized deployment
- **Cloud Integration**: AWS S3, Google Cloud Storage
- **Advanced Analytics**: Processing metrics and insights 