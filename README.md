# Smart Document Analyser

A powerful AI-powered document analysis tool that combines visual understanding and text analysis using multi-modal AI models. Built with **Ollama** for local LLM inference, **LangChain** for intelligent document processing chains, and **VectorDB** for semantic search and Q&A capabilities.

## 🚀 Features

- **Multi-modal Document Processing**: Handles PDFs, images, and screenshots
- **Visual Analysis**: Uses LLaVA models for document understanding
- **Text Analysis**: Powered by Mistral 7B for summarization and structured data extraction
- **Vector Database**: FAISS-based semantic search for intelligent Q&A
- **Modern Web Interface**: React-based UI with real-time processing feedback
- **Local AI Processing**: All processing happens locally via Ollama

## 🛠️ Technology Stack

- **Backend**: FastAPI with Python
- **Frontend**: React with TypeScript
- **AI Models**: 
  - Visual understanding - tested with: `llava:latest`
  - Text analysis - test with: `mistral:7b-instruct`
  (You can choose other models as well.)
- **Vector Database**: FAISS for semantic search
- **LLM Framework**: LangChain for intelligent processing chains
- **Local Inference**: Ollama for model serving

## 📋 Setup Instructions

1. **Create and activate the virtual environment using [uv](https://github.com/astral-sh/uv):**
   ```sh
   uv venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```sh
   uv sync
   ```

3. **Install and start Ollama:**
   ```sh
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required models
   ollama pull llava:latest
   ollama pull mistral:7b-instruct
   ```

4. **Environment Variables:**
   - Copy `.env.example` to `.env` and configure your settings
   - **Never commit your `.env` file to version control**

5. **Start the application:**
   ```sh
   # Backend
   python -m uvicorn src.app.main:app --reload
   
   # Frontend (in another terminal)
   cd frontend && npm run dev
   ```

## 🔧 Configuration

The application uses several AI models and services. While these are configurable, we recommend testing with these proven models:

- **LLAVA_MODEL**: Visual analysis model (recommended: `llava:latest`)
- **TEXT_MODEL**: Text processing model (recommended: `mistral:7b-instruct`)
- **OLLAMA_HOST**: Ollama server URL (default: `http://localhost:11434`)

### Recommended Model Setup

For optimal performance, we suggest using these tested and verified models:

```sh
# Visual understanding model
ollama pull llava:latest

# Text analysis model  
ollama pull mistral:7b-instruct
```

These models have been thoroughly tested and provide excellent results for document analysis tasks.

## 🎯 Usage

1. **Upload Documents**: Drag & drop PDFs or images
2. **Visual Analysis**: Automatic document understanding and description
3. **Text Extraction**: OCR processing with enhanced accuracy
4. **Structured Data**: Extract key information in JSON format
5. **Q&A Interface**: Ask questions about your documents
6. **Action Items**: Generate actionable tasks from content

## 🔒 Security

- Follow secure coding practices
- Validate all inputs
- Keep dependencies up-to-date
- Never expose secrets in version control

---

For detailed development information, see `CURSOR.local.md`. 