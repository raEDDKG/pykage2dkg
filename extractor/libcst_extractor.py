# extractor/libcst_extractor.py
import libcst as cst
from typing import Dict, List, Any, Optional


class LibCSTExtractor(cst.CSTVisitor):
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.packages = []
        self.type_annotations = {}
        self.comments = {}
        
    def visit_Import(self, node: cst.Import) -> None:
        """Extract import statements"""
        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                import_data = {
                    "@type": "Import",
                    "module": self._extract_module_name(name.name),
                    "alias": self._extract_alias(name.asname),
                    "text": cst.Module([cst.SimpleStatementLine([node])]).code.strip()
                }
                self.imports.append(import_data)
    
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Extract from import statements"""
        module_name = self._extract_module_name(node.module) if node.module else ""
        
        if isinstance(node.names, cst.ImportStar):
            import_data = {
                "@type": "ImportFrom",
                "module": module_name,
                "names": ["*"],
                "text": cst.Module([cst.SimpleStatementLine([node])]).code.strip()
            }
            self.imports.append(import_data)
        elif isinstance(node.names, (list, tuple)) or hasattr(node.names, '__iter__'):
            names = []
            for name in node.names:
                if isinstance(name, cst.ImportAlias):
                    names.append({
                        "name": self._extract_module_name(name.name),
                        "alias": self._extract_alias(name.asname)
                    })
            import_data = {
                "@type": "ImportFrom", 
                "module": module_name,
                "names": names,
                "text": cst.Module([cst.SimpleStatementLine([node])]).code.strip()
            }
            self.imports.append(import_data)
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Extract class definitions"""
        # Extract base classes
        bases = []
        if node.bases:
            for base in node.bases:
                if isinstance(base, cst.Arg):
                    bases.append(self._extract_expression(base.value))
        
        # Extract decorators
        decorators = [self._extract_decorator(dec) for dec in node.decorators]
        
        # Extract methods within the class
        methods = []
        for stmt in node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for inner_stmt in stmt.body:
                    if isinstance(inner_stmt, cst.FunctionDef):
                        methods.append(self._extract_method(inner_stmt, node.name.value))
            elif isinstance(stmt, cst.FunctionDef):
                methods.append(self._extract_method(stmt, node.name.value))
        
        class_data = {
            "@type": "Class",
            "name": node.name.value,
            "bases": bases,
            "decorators": decorators,
            "methods": methods,
            "docstring": self._extract_docstring(node),
            "text": cst.Module([node]).code.strip()
        }
        
        self.classes.append(class_data)
        
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        # Check if this is an async function
        is_async = node.asynchronous is not None
        self._extract_function_data(node, is_async=is_async)
    
    def _extract_function_data(self, node, is_async: bool = False):
        """Extract function data for both sync and async functions"""
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
            "isAsync": is_async,
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
    
    def _extract_module_name(self, node) -> str:
        """Extract module name from import node"""
        if node is None:
            return ""
        try:
            return cst.Module([cst.SimpleStatementLine([cst.Expr(node)])]).code.strip()
        except:
            return str(node)
    
    def _extract_alias(self, alias_node) -> Optional[str]:
        """Extract alias from import alias node"""
        if alias_node is None:
            return None
        try:
            return alias_node.name.value
        except:
            return str(alias_node)
    
    def _extract_expression(self, expr) -> str:
        """Extract expression as string"""
        try:
            return cst.Module([cst.SimpleStatementLine([cst.Expr(expr)])]).code.strip()
        except:
            return str(expr)
    
    def _extract_docstring(self, node) -> Optional[str]:
        """Extract docstring from class or function"""
        try:
            if hasattr(node, 'body') and hasattr(node.body, 'body') and node.body.body:
                first_stmt = node.body.body[0]
                if isinstance(first_stmt, cst.SimpleStatementLine) and first_stmt.body:
                    expr = first_stmt.body[0]
                    if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                        return expr.value.value.strip('"\'')
            return None
        except:
            return None
    
    def _extract_method(self, node: cst.FunctionDef, class_name: str) -> Dict[str, Any]:
        """Extract method information"""
        # Extract parameters
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
        
        # Extract decorators
        decorators = [self._extract_decorator(dec) for dec in node.decorators]
        
        # Check if this is an async method
        is_async = node.asynchronous is not None
        
        method_data = {
            "@type": "Method",
            "name": node.name.value,
            "parameters": params,
            "returnType": return_type,
            "decorators": decorators,
            "inClass": class_name,
            "isAsync": is_async,
            "docstring": self._extract_docstring(node),
            "text": cst.Module([node]).code.strip()
        }
        
        return method_data

def extract_with_libcst(source_code: str) -> Dict[str, Any]:
    """Enhanced extraction using LibCST for precise type information"""
    try:
        tree = cst.parse_expression(source_code) if '\n' not in source_code else cst.parse_module(source_code)
        extractor = LibCSTExtractor()
        tree.visit(extractor)
        return {
            "functions": extractor.functions,
            "classes": extractor.classes,
            "imports": extractor.imports,
            "packages": extractor.packages,
            "typeAnnotations": extractor.type_annotations,
            "extractionStatus": "success"
        }
    except cst.ParserError as e:
        print(f"LibCST parser error: {e}")
        return {
            "functions": [], "classes": [], "imports": [], "packages": [], 
            "typeAnnotations": {}, "parseError": str(e), "errorType": "syntax",
            "extractionStatus": "partial"
        }
    except Exception as e:
        print(f"LibCST extraction failed: {e}")
        return {
            "functions": [], "classes": [], "imports": [], "packages": [], 
            "typeAnnotations": {}, "parseError": str(e), "errorType": "unknown",
            "extractionStatus": "failed"
        }