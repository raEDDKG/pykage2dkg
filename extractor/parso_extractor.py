# extractor/parso_extractor.py
import parso
from typing import Dict, List, Any



class ParsoExtractor:
    def __init__(self):
        self.grammar = parso.load_grammar(version="3.9")
    
    def extract_with_error_recovery(self, source_code: str) -> Dict[str, Any]:
        """Parse code with error recovery for incomplete files"""
        try:
            tree = self.grammar.parse(source_code, error_recovery=True)
            return self._extract_from_tree(tree)
        except Exception as e:
            print(f"Parso parsing failed: {e}")
            return {"functions": [], "classes": [], "errors": [str(e)]}
    
    def _extract_from_tree(self, tree) -> Dict[str, Any]:
        functions = []
        classes = []
        errors = []
        
        for node in tree.get_first_leaf().get_next_siblings():
            if node.type == 'funcdef':
                func_data = self._extract_function(node)
                if func_data:
                    functions.append(func_data)
            elif node.type == 'classdef':
                class_data = self._extract_class(node)
                if class_data:
                    classes.append(class_data)
            elif hasattr(node, 'get_error'):
                errors.append(str(node.get_error()))
        
        return {
            "functions": functions,
            "classes": classes,
            "parseErrors": errors,
            "isPartialParse": len(errors) > 0
        }
    
    def _extract_function(self, node) -> Dict[str, Any]:
        try:
            name = node.children[1].value if len(node.children) > 1 else "unknown"
            return {
                "@type": "Function",
                "name": name,
                "startLine": node.start_pos[0],
                "endLine": node.end_pos[0],
                "isErrorRecovered": hasattr(node, 'get_error')
            }
        except Exception:
            return None
    
    def _extract_class(self, node) -> Dict[str, Any]:
        try:
            name = node.children[1].value if len(node.children) > 1 else "unknown"
            return {
                "@type": "Class",
                "name": name,
                "startLine": node.start_pos[0],
                "endLine": node.end_pos[0],
                "isErrorRecovered": hasattr(node, 'get_error')
            }
        except Exception:
            return None