try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    
    # Try multiple models in order of preference
    MODEL_OPTIONS = [
        "microsoft/CodeT5-small",  # Smaller, more stable model
        "Salesforce/codet5p-220m",  # Original choice
        "microsoft/codebert-base"   # Fallback option
    ]
    
    TRANSFORMERS_AVAILABLE = False
    tokenizer = None
    model = None
    
    for model_id in MODEL_OPTIONS:
        try:
            print(f"🔄 Attempting to load model: {model_id}")
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
            TRANSFORMERS_AVAILABLE = True
            print(f"✅ Successfully loaded code summarization model: {model_id}")
            break
        except Exception as e:
            print(f"⚠️ Could not load model {model_id}: {e}")
            continue
    
    if not TRANSFORMERS_AVAILABLE:
        print("❌ Could not load any transformer models, using fallback summarizer")
        
except ImportError:
    print("Warning: transformers not available, using fallback code summarizer")
    TRANSFORMERS_AVAILABLE = False

def summarize_code(code: str) -> str:
    """
    Generate a concise summary of a code snippet.
    """
    if not code or not code.strip():
        return "Empty code"
    
    # Clean and validate input
    code = code.strip()
    if len(code) > 10000:  # Limit very long inputs
        code = code[:10000] + "..."
    
    if not TRANSFORMERS_AVAILABLE:
        return _fallback_summarize(code)
    
    try:
        # Use a more appropriate prompt for code summarization
        # Remove the problematic "summarize:" prefix that causes recursion
        prompt = f"# Code Summary\n{code}\n\n# What this code does:"
        
        inputs = tokenizer.encode(prompt,
                                  return_tensors="pt",
                                  truncation=True,
                                  max_length=400)  # Reduced to leave room for output
        
        summary_ids = model.generate(
            inputs,
            max_length=150,  # Increased for more complete summaries
            min_length=10,
            length_penalty=1.5,  # Reduced to allow longer summaries
            num_beams=3,  # Reduced for faster generation
            early_stopping=True,
            do_sample=False,  # Disable sampling for more deterministic output
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        # Clean up the output
        summary = _clean_summary(summary, prompt)
        
        # Validate the summary
        if _is_valid_summary(summary):
            return summary
        else:
            print(f"Warning: Generated invalid summary, falling back to rule-based approach")
            return _fallback_summarize(code)
            
    except Exception as e:
        print(f"Warning: Code summarization failed: {e}, using fallback")
        return _fallback_summarize(code)

def _fallback_summarize(code: str) -> str:
    """
    Fallback rule-based summarization when transformers fail or are unavailable.
    """
    lines = code.strip().split('\n')
    if not lines:
        return "Empty code"
    
    # Extract function/class names and docstrings
    summary_parts = []
    in_docstring = False
    docstring_content = []
    
    for line in lines:
        line = line.strip()
        
        # Handle docstrings
        if line.startswith('"""') or line.startswith("'''"):
            if in_docstring:
                # End of docstring
                docstring = " ".join(docstring_content).strip()
                if docstring and len(docstring) > 10:
                    summary_parts.append(docstring[:100])  # Limit docstring length
                in_docstring = False
                docstring_content = []
            else:
                # Start of docstring
                in_docstring = True
                # Check if it's a single-line docstring
                quote_type = '"""' if line.startswith('"""') else "'''"
                if line.count(quote_type) >= 2:
                    # Single-line docstring
                    docstring = line.strip(quote_type).strip()
                    if docstring and len(docstring) > 10:
                        summary_parts.append(docstring[:100])
                else:
                    # Multi-line docstring start
                    content = line.replace(quote_type, '').strip()
                    if content:
                        docstring_content.append(content)
        elif in_docstring:
            # Inside a multi-line docstring
            docstring_content.append(line)
        elif line.startswith('def ') or line.startswith('async def '):
            # Function definition
            func_name = line.split('(')[0].replace('def ', '').replace('async def ', '').strip()
            summary_parts.append(f"Defines function '{func_name}'")
        elif line.startswith('class '):
            # Class definition
            class_name = line.split('(')[0].split(':')[0].replace('class ', '').strip()
            summary_parts.append(f"Defines class '{class_name}'")
        elif line.startswith('return ') and len(line) < 50:
            # Return statement (if short)
            summary_parts.append(f"Returns {line[7:].strip()}")
    
    if summary_parts:
        return "; ".join(summary_parts[:2])  # Limit to first 2 items for conciseness
    else:
        # Analyze code structure if no obvious patterns found
        if 'def ' in code:
            func_count = code.count('def ')
            return f"Contains {func_count} function(s)"
        elif 'class ' in code:
            class_count = code.count('class ')
            return f"Contains {class_count} class(es)"
        else:
            return f"Code snippet ({len(lines)} lines)"

def _clean_summary(summary: str, original_prompt: str) -> str:
    """
    Clean up the generated summary to remove artifacts and improve quality.
    """
    # Remove the original prompt from the output
    if original_prompt in summary:
        summary = summary.replace(original_prompt, "").strip()
    
    # Remove common artifacts
    artifacts = [
        "# Code Summary",
        "# What this code does:",
        "summarize:",
        "Summary:",
        "This code",
        "The code"
    ]
    
    for artifact in artifacts:
        if summary.startswith(artifact):
            summary = summary[len(artifact):].strip()
    
    # Remove repetitive patterns
    words = summary.split()
    if len(words) > 3:
        # Check for repetitive patterns
        for i in range(len(words) - 2):
            if words[i] == words[i+1] == words[i+2]:
                # Found repetition, truncate
                summary = " ".join(words[:i])
                break
    
    # Ensure it starts with a capital letter and ends properly
    if summary:
        summary = summary[0].upper() + summary[1:] if len(summary) > 1 else summary.upper()
        if not summary.endswith('.'):
            summary += '.'
    
    return summary.strip()

def _is_valid_summary(summary: str) -> bool:
    """
    Validate that the generated summary is reasonable.
    """
    if not summary or len(summary.strip()) < 5:
        return False
    
    # Check for problematic patterns
    problematic_patterns = [
        "summarize(summarize",
        "def __call__",
        "Licensed to the Apache",
        "/*",
        "*/",
        "summarize: def",
        "return True\n\nsummarize"
    ]
    
    for pattern in problematic_patterns:
        if pattern in summary:
            return False
    
    # Check for excessive repetition
    words = summary.split()
    if len(words) > 5:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Too much repetition
            return False
    
    return True
