import os
from typing import Optional
from langchain_ollama import OllamaLLM, OllamaEmbeddings

class ModelManager:
    """Singleton model manager for efficient LLM instance reuse"""
    
    _instance = None
    _llm_instance = None
    _embeddings_instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._initialize_models()
    
    def _initialize_models(self):
        """Initialize model instances with proper configuration"""
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        text_model = os.getenv("TEXT_MODEL", "mistral:7b-instruct")
        
        # Initialize LLM with optimized settings
        self._llm_instance = OllamaLLM(
            model=text_model,
            base_url=ollama_host,
            temperature=0.1,  # Lower temperature for more consistent results
            timeout=120,  # Increased timeout for reliability
            num_ctx=4096,  # Context window size
        )
        
        # Initialize embeddings with optimized settings
        self._embeddings_instance = OllamaEmbeddings(
            model=text_model,
            base_url=ollama_host,
        )
    
    @property
    def llm(self) -> OllamaLLM:
        """Get the shared LLM instance"""
        if self._llm_instance is None:
            self._initialize_models()
        return self._llm_instance
    
    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Get the shared embeddings instance"""
        if self._embeddings_instance is None:
            self._initialize_models()
        return self._embeddings_instance
    
    def warm_up_models(self):
        """Warm up models to reduce first-call latency"""
        try:
            # Simple warm-up call to initialize models
            test_prompt = "Hello"
            self.llm.invoke(test_prompt)
            print("Models warmed up successfully")
        except Exception as e:
            print(f"Model warm-up failed: {e}")
    
    def reset_models(self):
        """Reset model instances (useful for testing or error recovery)"""
        self._llm_instance = None
        self._embeddings_instance = None
        self._initialize_models()

# Global model manager instance
model_manager = ModelManager() 