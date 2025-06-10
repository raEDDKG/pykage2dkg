import os
from collections import defaultdict
from .function_extractor import FunctionExtractor
from .codebert_summarizer import summarize_code
from .codebert_embedder import embed_code

def build_codefile(rel_path, code):
    extractor = FunctionExtractor()
    classes, top_level = extractor.extract(code)

    for cls in classes:
        for fn in cls["hasPart"]:
            fn["summary"]   = summarize_code(fn["text"])
            fn["embedding"] = embed_code(fn["text"])
    for fn in top_level:
        fn["summary"]   = summarize_code(fn["text"])
        fn["embedding"] = embed_code(fn["text"])

    return {
        "@type": "CodeFile",
        "name": rel_path,
        "programmingLanguage": "Python",
        "text": code,
        "hasPart": classes + top_level
    }

def walk_python_modules(base_path):
    modules = defaultdict(list)
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel  = os.path.relpath(full, base_path)
                with open(full, encoding="utf-8", errors="ignore") as fh:
                    src = fh.read()
                modules[os.path.relpath(root, base_path)].append(
                    build_codefile(rel, src)
                )
    return [
        {"@type": "CodeModule", "name": mod if mod!="." else "", "hasPart": cps}
        for mod, cps in modules.items()
    ]