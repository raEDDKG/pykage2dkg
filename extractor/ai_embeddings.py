"""
AI-Optimized Embeddings Module

Provides multiple embedding formats for different AI agents:
- sentence-transformers (universal compatibility)
- OpenAI-compatible format
- Hugging Face transformers format
- Custom embedding metadata

Features:
- Configurable embedding models
- Multiple output formats
- Embedding metadata for AI agents
- Fallback options when models unavailable
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Union
import warnings

class AIEmbeddingGenerator:
    """Generate AI-compatible embeddings with multiple format support"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedder = None
        self.embedding_dim = None
        self.model_type = self._detect_model_type(model_name)
        
        # Initialize the appropriate embedder
        self._initialize_embedder()
    
    def _detect_model_type(self, model_name: str) -> str:
        """Detect the type of embedding model"""
        if model_name.startswith("sentence-transformers/"):
            return "sentence-transformers"
        elif model_name.startswith("openai/"):
            return "openai"
        elif model_name.startswith("huggingface/"):
            return "huggingface"
        else:
            return "sentence-transformers"  # Default
    
    def _initialize_embedder(self):
        """Initialize the appropriate embedding model"""
        try:
            if self.model_type == "sentence-transformers":
                self._init_sentence_transformers()
            elif self.model_type == "openai":
                self._init_openai()
            elif self.model_type == "huggingface":
                self._init_huggingface()
        except Exception as e:
            print(f"⚠️ Failed to initialize {self.model_type} embedder: {e}")
            self.embedder = None
    
    def _init_sentence_transformers(self):
        """Initialize sentence-transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(self.model_name)
            
            # Get embedding dimension
            test_embedding = self.embedder.encode(["test"])
            self.embedding_dim = test_embedding.shape[1]
            
            print(f"✅ Loaded sentence-transformers model: {self.model_name} (dim: {self.embedding_dim})")
            
        except ImportError:
            print("⚠️ sentence-transformers not available. Install with: pip install sentence-transformers")
            raise
    
    def _init_openai(self):
        """Initialize OpenAI embeddings"""
        try:
            import openai
            # OpenAI initialization would go here
            print("⚠️ OpenAI embeddings not yet implemented")
            raise NotImplementedError("OpenAI embeddings not yet implemented")
        except ImportError:
            print("⚠️ openai not available. Install with: pip install openai")
            raise
    
    def _init_huggingface(self):
        """Initialize Hugging Face transformers model"""
        try:
            from transformers import AutoTokenizer, AutoModel
            # Hugging Face initialization would go here
            print("⚠️ Hugging Face embeddings not yet implemented")
            raise NotImplementedError("Hugging Face embeddings not yet implemented")
        except ImportError:
            print("⚠️ transformers not available. Install with: pip install transformers")
            raise
    
    def generate_embeddings(self, texts: List[str], 
                          formats: List[str] = ["sentence-transformers"]) -> Dict[str, Any]:
        """
        Generate embeddings in multiple formats
        
        Args:
            texts: List of texts to embed
            formats: List of output formats ["sentence-transformers", "openai", "numpy", "list"]
        
        Returns:
            Dictionary with embeddings in requested formats plus metadata
        """
        
        if not self.embedder:
            return self._create_fallback_response(texts, formats)
        
        try:
            # Generate base embeddings
            embeddings = self.embedder.encode(texts)
            
            # Convert to requested formats
            result = {
                "metadata": self._create_embedding_metadata(texts, embeddings),
                "embeddings": {}
            }
            
            for format_type in formats:
                result["embeddings"][format_type] = self._convert_to_format(embeddings, format_type)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            return self._create_fallback_response(texts, formats)
    
    def _convert_to_format(self, embeddings: np.ndarray, format_type: str) -> Any:
        """Convert embeddings to specific format"""
        
        if format_type == "sentence-transformers":
            return embeddings.tolist()
        
        elif format_type == "numpy":
            return embeddings
        
        elif format_type == "list":
            return embeddings.tolist()
        
        elif format_type == "openai":
            # OpenAI format (list of lists)
            return embeddings.tolist()
        
        elif format_type == "huggingface":
            # Hugging Face format
            return embeddings.tolist()
        
        else:
            return embeddings.tolist()  # Default to list
    
    def _create_embedding_metadata(self, texts: List[str], embeddings: np.ndarray) -> Dict[str, Any]:
        """Create comprehensive embedding metadata for AI agents"""
        
        return {
            "@type": "EmbeddingMetadata",
            "model": {
                "name": self.model_name,
                "type": self.model_type,
                "provider": self._get_model_provider(),
                "dimensions": self.embedding_dim,
                "maxSequenceLength": self._get_max_sequence_length()
            },
            "data": {
                "textCount": len(texts),
                "embeddingShape": list(embeddings.shape),
                "dataType": str(embeddings.dtype)
            },
            "aiCompatibility": {
                "sentenceTransformers": True,
                "openai": True,
                "huggingface": True,
                "vectorDatabases": ["pinecone", "weaviate", "chroma", "faiss"],
                "frameworks": ["langchain", "llamaindex", "haystack"]
            },
            "usage": {
                "semanticSearch": True,
                "clustering": True,
                "classification": True,
                "similarityComparison": True
            },
            "performance": {
                "modelSize": self._estimate_model_size(),
                "inferenceSpeed": "fast" if self.embedding_dim <= 384 else "medium"
            }
        }
    
    def _get_model_provider(self) -> str:
        """Get the model provider"""
        if "sentence-transformers" in self.model_name:
            return "sentence-transformers"
        elif "openai" in self.model_name:
            return "openai"
        elif "huggingface" in self.model_name:
            return "huggingface"
        else:
            return "unknown"
    
    def _get_max_sequence_length(self) -> int:
        """Get maximum sequence length for the model"""
        if hasattr(self.embedder, 'max_seq_length'):
            return self.embedder.max_seq_length
        elif "all-MiniLM" in self.model_name:
            return 256
        elif "all-mpnet" in self.model_name:
            return 384
        else:
            return 512  # Default
    
    def _estimate_model_size(self) -> str:
        """Estimate model size category"""
        if "MiniLM" in self.model_name:
            return "small"
        elif "base" in self.model_name:
            return "medium"
        elif "large" in self.model_name:
            return "large"
        else:
            return "unknown"
    
    def _create_fallback_response(self, texts: List[str], formats: List[str]) -> Dict[str, Any]:
        """Create fallback response when embeddings can't be generated"""
        
        fallback_embeddings = {}
        for format_type in formats:
            # Create dummy embeddings (zeros) for compatibility
            dummy_embedding = [[0.0] * 384 for _ in texts]  # 384-dim like MiniLM
            fallback_embeddings[format_type] = dummy_embedding
        
        return {
            "metadata": {
                "@type": "EmbeddingMetadata",
                "status": "fallback",
                "reason": "Embedding model not available",
                "model": {
                    "name": self.model_name,
                    "type": self.model_type,
                    "available": False
                },
                "fallback": {
                    "type": "zero_embeddings",
                    "dimensions": 384,
                    "note": "AI agents should generate their own embeddings from the text content"
                },
                "aiCompatibility": {
                    "recommendation": "Install sentence-transformers for proper embeddings",
                    "alternatives": [
                        "Use OpenAI embeddings API",
                        "Use Hugging Face transformers",
                        "Generate embeddings client-side"
                    ]
                }
            },
            "embeddings": fallback_embeddings
        }

def enhance_jsonld_with_ai_embeddings(jsonld: Dict[str, Any], 
                                    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                                    formats: List[str] = ["sentence-transformers"]) -> Dict[str, Any]:
    """
    Enhance JSON-LD with AI-compatible embeddings
    
    Args:
        jsonld: The JSON-LD document to enhance
        embedding_model: Model name for embeddings
        formats: List of embedding formats to generate
    
    Returns:
        Enhanced JSON-LD with embeddings
    """
    
    # Initialize embedding generator
    embedder = AIEmbeddingGenerator(embedding_model)
    
    # Extract texts for embedding
    texts_to_embed = []
    text_sources = []
    
    # Package description
    if jsonld.get("description"):
        texts_to_embed.append(f"Package: {jsonld.get('name', 'unknown')}. {jsonld['description']}")
        text_sources.append("package_description")
    
    # Function and class descriptions
    for module in jsonld.get("hasPart", []):
        for item in module.get("hasPart", []):
            if item.get("@type") in ["Function", "Class"] and item.get("description"):
                text = f"{item['@type']}: {item['name']}. {item['description']}"
                texts_to_embed.append(text)
                text_sources.append(f"{item['@type'].lower()}_{item['name']}")
    
    # Limit to reasonable number for performance
    max_embeddings = 20
    if len(texts_to_embed) > max_embeddings:
        texts_to_embed = texts_to_embed[:max_embeddings]
        text_sources = text_sources[:max_embeddings]
    
    # Generate embeddings
    if texts_to_embed:
        embedding_result = embedder.generate_embeddings(texts_to_embed, formats)
        
        # Add to JSON-LD
        jsonld["aiEmbeddings"] = {
            "@type": "AIEmbeddings",
            "textSources": text_sources,
            "texts": texts_to_embed,
            **embedding_result
        }
    else:
        # No texts to embed
        jsonld["aiEmbeddings"] = {
            "@type": "AIEmbeddings",
            "status": "no_content",
            "reason": "No suitable text content found for embedding"
        }
    
    return jsonld

# Convenience functions for different AI frameworks

def get_langchain_compatible_embeddings(jsonld: Dict[str, Any]) -> Optional[List[List[float]]]:
    """Extract embeddings in LangChain-compatible format"""
    ai_embeddings = jsonld.get("aiEmbeddings", {})
    embeddings = ai_embeddings.get("embeddings", {})
    return embeddings.get("sentence-transformers") or embeddings.get("list")

def get_openai_compatible_embeddings(jsonld: Dict[str, Any]) -> Optional[List[List[float]]]:
    """Extract embeddings in OpenAI-compatible format"""
    ai_embeddings = jsonld.get("aiEmbeddings", {})
    embeddings = ai_embeddings.get("embeddings", {})
    return embeddings.get("openai") or embeddings.get("sentence-transformers")

def get_embedding_metadata(jsonld: Dict[str, Any]) -> Dict[str, Any]:
    """Extract embedding metadata for AI agent decision making"""
    ai_embeddings = jsonld.get("aiEmbeddings", {})
    return ai_embeddings.get("metadata", {})