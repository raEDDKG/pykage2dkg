from transformers import AutoTokenizer, AutoModel
import torch

# Public CodeBERT for embeddings
deembed_MODEL_ID = "neulab/codebert-python"

tokenizer_embed = AutoTokenizer.from_pretrained(deembed_MODEL_ID)
model_embed     = AutoModel.from_pretrained(deembed_MODEL_ID)

def embed_code(code: str) -> list[float]:
    """
    Returns a fixed-size embedding vector for the code.
    """
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

