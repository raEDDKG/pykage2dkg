try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    
    # Best code-focused embedding model - Microsoft's CodeBERT
    # Alternative: "microsoft/unixcoder-base" for even better code understanding
    EMBED_MODEL_ID = "microsoft/codebert-base"
    
    try:
        tokenizer_embed = AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
        model_embed = AutoModel.from_pretrained(EMBED_MODEL_ID)
        TRANSFORMERS_AVAILABLE = True
        print(f"✅ Loaded code embedding model: {EMBED_MODEL_ID}")
    except Exception as e:
        print(f"Warning: Could not load code embedding model {EMBED_MODEL_ID}: {e}")
        TRANSFORMERS_AVAILABLE = False
        
except ImportError:
    print("Warning: transformers not available, using fallback code embedder")
    TRANSFORMERS_AVAILABLE = False

def embed_code(code: str) -> list[float]:
    """
    Returns a fixed-size embedding vector for the code.
    Handles large functions with intelligent chunking.
    """
    if not TRANSFORMERS_AVAILABLE:
        return _fallback_embedding(code)
    
    # Check if code is small enough for single embedding
    if len(code) <= 2000:  # Reasonable size for single embedding
        return _embed_single(code)
    else:
        # Large function - use hierarchical approach
        return _embed_hierarchical(code)

def _fallback_embedding(code: str) -> list[float]:
    """Fallback embedding when transformers not available"""
    import hashlib
    
    # Create a simple feature vector based on code characteristics
    features = [0.0] * 768  # Match typical transformer embedding size
    
    # Basic features
    features[0] = len(code) / 1000.0  # Normalized length
    features[1] = code.count('\n') / 100.0  # Normalized line count
    features[2] = code.count('def ') / 10.0  # Function count
    features[3] = code.count('class ') / 10.0  # Class count
    features[4] = code.count('import ') / 10.0  # Import count
    features[5] = code.count('async ') / 10.0  # Async count
    
    # Hash-based features for the rest
    hash_obj = hashlib.md5(code.encode())
    hash_bytes = hash_obj.digest()
    
    for i in range(6, min(len(features), 6 + len(hash_bytes))):
        features[i] = hash_bytes[i - 6] / 255.0
    
    return features

def _embed_single(code: str) -> list[float]:
    """Embed a single piece of code"""
    tokens = tokenizer_embed(
        code,
        return_tensors="pt",
        max_length=512,
        truncation=True,
        padding="max_length"
    )
    outputs = model_embed(**tokens)
    emb = outputs.last_hidden_state.mean(dim=1).squeeze().detach().cpu().tolist()
    return emb

def _embed_hierarchical(code: str) -> list[float]:
    """Embed large code using hierarchical chunking"""
    import numpy as np
    
    # Split into logical chunks
    chunks = _split_code_intelligently(code)
    
    if not chunks:
        return _embed_single(code[:2000])  # Fallback to truncation
    
    # Embed each chunk
    chunk_embeddings = []
    for chunk in chunks:
        if chunk.strip():  # Skip empty chunks
            emb = _embed_single(chunk)
            chunk_embeddings.append(emb)
    
    if not chunk_embeddings:
        return _embed_single(code[:2000])  # Fallback
    
    # Combine embeddings (average)
    return np.mean(chunk_embeddings, axis=0).tolist()

def _split_code_intelligently(code: str) -> list[str]:
    """Split code into logical chunks for embedding"""
    import ast
    
    try:
        # Try to parse and split by functions/classes
        tree = ast.parse(code)
        chunks = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                try:
                    chunk = ast.get_source_segment(code, node)
                    if chunk and len(chunk) <= 2000:
                        chunks.append(chunk)
                    elif chunk:
                        # Further split large functions
                        chunks.extend(_split_by_lines(chunk, 1500))
                except:
                    continue
        
        if chunks:
            return chunks
    except:
        pass
    
    # Fallback: split by lines
    return _split_by_lines(code, 1500)

def _split_by_lines(code: str, max_chars: int) -> list[str]:
    """Split code by lines, respecting character limits"""
    lines = code.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line) + 1  # +1 for newline
        
        if current_size + line_size > max_chars and current_chunk:
            # Start new chunk
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks

