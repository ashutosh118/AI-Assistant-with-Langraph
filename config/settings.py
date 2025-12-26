from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"  # Change to your preferred model
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    
    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "./vector_store"
    FAISS_INDEX_PATH: str = "./vector_store/faiss_index"
    
    # Agent Configuration
    MAX_SEARCH_RESULTS: int = 5
    MAX_SCRAPING_PAGES: int = 3
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # UI Configuration
    PAGE_TITLE: str = "Welcome Mr. Srivastava"
    PAGE_ICON: str = "🤖"
    LAYOUT: str = "wide"
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 200  # MB
    SUPPORTED_FILE_TYPES: list = ['.txt', '.pdf', '.docx', '.csv', '.json']
    
    @classmethod
    def get_agent_prompts(cls) -> Dict[str, str]:
        """Return agent-specific prompts"""
        return {
            "web_search": """You are a web search specialist. Your task is to search for relevant information on the web based on user queries. 
            Provide accurate, up-to-date information with proper citations.""",
            
            "web_scraper": """You are a web scraping expert. Extract meaningful content from web pages, focusing on the most relevant information. 
            Structure the extracted data clearly and remove unnecessary elements.""",
            
            "file_reader": """You are a file processing expert. Read and analyze various file formats, extract key information, 
            and present it in a structured manner.""",
            
            "summarizer": """You are a summarization expert. Create concise, informative summaries that capture the essential points 
            while maintaining context and clarity.""",
            
            "elaborator": """You are an elaboration specialist. Expand on topics with detailed explanations, examples, and additional context 
            to provide comprehensive understanding.""",
            
            "calculator": """You are a mathematical computation expert. Perform accurate calculations, solve mathematical problems, 
            and provide step-by-step solutions when needed.""",
            
            "predictor": """You are a prediction and analysis expert. Analyze data patterns, make informed predictions, 
            and provide insights based on available information."""
        }

settings = Settings()
