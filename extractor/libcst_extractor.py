# extractor/libcst_extractor.py
import libcst as cst
from typing import Dict, List, Any, Optional


class LibCSTExtractor(cst.CSTVisitor):
    def __init__(self):
        self.functions = []
        self.classes = []
        self.type_annotations = {}
        self.comments = {}
        
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        # Extract type annotations
        params = []
        for param in node.params.params:
            param_info = {
                "name": param.name.value,
                "annotation": self._extract_annotation(param.annotation),
                "default": self._extract_default(param.default)
            }
            params.append(param_info)
        
        # Extract return type
        return_type = self._extract_annotation(node.returns)
        
        # Extract leading comments
        leading_lines = node.leading_lines
        comments = [line.comment.value for line in leading_lines 
                   if hasattr(line, 'comment') and line.comment]
        
        function_data = {
            "@type": "Function",
            "name": node.name.value,
            "parameters": params,
            "returnType": return_type,
            "typeComments": comments,
            "isAsync": isinstance(node, cst.AsyncFunctionDef),
            "decorators": [self._extract_decorator(dec) for dec in node.decorators]
        }
        
        self.functions.append(function_data)
    
    def _extract_annotation(self, annotation: Optional[cst.Annotation]) -> Optional[str]:
        if annotation is None:
            return None
        return cst.Module([cst.SimpleStatementLine([cst.Expr(annotation.annotation)])]).code.strip()
    
    def _extract_default(self, default: Optional[cst.AssignTarget]) -> Optional[str]:
        if default is None:
            return None
        return cst.Module([cst.SimpleStatementLine([cst.Expr(default)])]).code.strip()
    
    def _extract_decorator(self, decorator: cst.Decorator) -> str:
        return cst.Module([cst.SimpleStatementLine([cst.Expr(decorator.decorator)])]).code.strip()

def extract_with_libcst(source_code: str) -> Dict[str, Any]:
    """Enhanced extraction using LibCST for precise type information"""
    try:
        tree = cst.parse_expression(source_code) if '\n' not in source_code else cst.parse_module(source_code)
        extractor = LibCSTExtractor()
        tree.visit(extractor)
        return {
            "functions": extractor.functions,
            "classes": extractor.classes,
            "typeAnnotations": extractor.type_annotations
        }
    except Exception as e:
        print(f"LibCST extraction failed: {e}")
        return {"functions": [], "classes": [], "typeAnnotations": {}}