# extractor/file_walker.py

from .function_extractor import extract_functions_from_code
from .codebert_summarizer import summarize_code
import os

def walk_python_files(base_path):
    files = []
    for root, _, filenames in os.walk(base_path):
        for f in filenames:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, base_path)
                with open(full_path, encoding="utf-8", errors="ignore") as file:
                    code = file.read()

                functions = extract_functions_from_code(code, rel_path)
                for fn in functions:
                    fn["summary"] = summarize_code(fn["code"])

                files.append({
                    "@type": "CodeFile",
                    "name": rel_path,
                    "programmingLanguage": "Python",
                    "text": code,
                    "functions": functions  # Optional extension to schema
                })
    return files
