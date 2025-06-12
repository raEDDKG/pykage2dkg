try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    
    # Best code-focused summarization model - CodeT5+ for better code understanding
    # Alternative: "Salesforce/codet5p-220m-py" for Python-specific summarization
    SUMMARY_MODEL_ID = "Salesforce/codet5p-220m"
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL_ID)
        model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARY_MODEL_ID)
        TRANSFORMERS_AVAILABLE = True
        print(f"✅ Loaded code summarization model: {SUMMARY_MODEL_ID}")
    except Exception as e:
        print(f"Warning: Could not load code summarization model {SUMMARY_MODEL_ID}: {e}")
        TRANSFORMERS_AVAILABLE = False
        
except ImportError:
    print("Warning: transformers not available, using fallback code summarizer")
    TRANSFORMERS_AVAILABLE = False

def summarize_code(code: str) -> str:
    """
    Generate a concise summary of a code snippet.
    """
    if not TRANSFORMERS_AVAILABLE:
        # Fallback: simple rule-based summarization
        lines = code.strip().split('\n')
        if not lines:
            return "Empty code"
        
        # Extract function/class names and docstrings
        summary_parts = []
        for line in lines:
            line = line.strip()
            if line.startswith('def ') or line.startswith('async def '):
                func_name = line.split('(')[0].replace('def ', '').replace('async def ', '')
                summary_parts.append(f"Function: {func_name}")
            elif line.startswith('class '):
                class_name = line.split('(')[0].replace('class ', '').replace(':', '')
                summary_parts.append(f"Class: {class_name}")
            elif line.startswith('"""') or line.startswith("'''"):
                docstring = line.strip('"""').strip("'''").strip()
                if docstring:
                    summary_parts.append(docstring)
        
        if summary_parts:
            return "; ".join(summary_parts[:3])  # Limit to first 3 items
        else:
            return f"Code snippet ({len(lines)} lines)"
    
    # Use transformers if available
    prefix = "summarize: "
    inputs = tokenizer.encode(prefix + code,
                              return_tensors="pt",
                              truncation=True,
                              max_length=512)
    summary_ids = model.generate(
        inputs,
        max_length=64,
        min_length=5,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
