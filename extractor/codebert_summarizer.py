from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Use a public summarization model
MODEL_ID = "Salesforce/codet5-base-multi-sum"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)

def summarize_code(code: str) -> str:
    """
    Generate a concise summary of a code snippet.
    """
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
