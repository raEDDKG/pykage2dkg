try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    
    # Public CodeBERT for embeddings
    deembed_MODEL_ID = "neulab/codebert-python"
    
    try:
        tokenizer_embed = AutoTokenizer.from_pretrained(deembed_MODEL_ID)
        model_embed = AutoModel.from_pretrained(deembed_MODEL_ID)
        TRANSFORMERS_AVAILABLE = True
    except Exception as e:
        print(f"Warning: Could not load transformers model: {e}")
        TRANSFORMERS_AVAILABLE = False
        
except ImportError:
    print("Warning: transformers not available, using fallback embedder")
    TRANSFORMERS_AVAILABLE = False

def embed_code(code: str) -> list[float]:
    """
    Returns a fixed-size embedding vector for the code.
    """
    if not TRANSFORMERS_AVAILABLE:
        # Fallback: simple hash-based embedding
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
    
    # Use transformers if available
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

