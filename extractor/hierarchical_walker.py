import os
from collections import defaultdict
from datetime import datetime
from .function_extractor import EnhancedFunctionExtractor
from .treesitter_extractor import TreeSitterExtractor
from .dossier_extractor import DossierExtractor
from .codebert_summarizer import summarize_code
from .codebert_embedder import embed_code

def build_enhanced_codefile(rel_path, code, base_path):
    extractor = EnhancedFunctionExtractor()
    enhanced = extractor.extract_enhanced(code, os.path.join(base_path, rel_path))
    classes = enhanced['ast']['classes']
    top_level = enhanced['ast']['functions']
    for cls in classes:
        for fn in cls['hasPart']:
            fn['summary']   = summarize_code(fn['text'])
            fn['embedding'] = embed_code(fn['text'])
    for fn in top_level:
        fn['summary']   = summarize_code(fn['text'])
        fn['embedding'] = embed_code(fn['text'])
    ts_data = TreeSitterExtractor().extract_from_file(os.path.join(base_path, rel_path))
    doc_data = DossierExtractor().extract_documentation(base_path)
    return {
        "@type": "CodeFile",
        "name": rel_path,
        "programmingLanguage": "Python",
        "text": code,
        "hasPart": classes + top_level,
        "enhanced": enhanced,
        "crossLanguage": ts_data,
        "documentation": doc_data,
        "analysisTimestamp": datetime.utcnow().isoformat()
    }

def walk_python_modules_enhanced(base_path):
    modules = defaultdict(list)
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith('.py'):
                full = os.path.join(root, f)
                rel  = os.path.relpath(full, base_path)
                with open(full, encoding='utf-8', errors='ignore') as fh:
                    src = fh.read()
                modules[os.path.relpath(root, base_path)].append(
                    build_enhanced_codefile(rel, src, base_path)
                )
    return [
        {"@type": "CodeModule", "name": mod if mod!='.' else '', "hasPart": cps}
        for mod, cps in modules.items()
    ]