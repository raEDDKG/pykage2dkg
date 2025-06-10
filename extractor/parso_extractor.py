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
            return {"functions": [], "classes": [], "imports": [], "packages": [], "errors": [str(e)]}
    
    def _extract_from_tree(self, tree) -> Dict[str, Any]:
        functions = []
        classes = []
        imports = []
        packages = []
        errors = []
        
        # Walk through all nodes in the tree
        for node in self._walk_tree(tree):
            if node.type == 'funcdef':
                func_data = self._extract_function(node)
                if func_data:
                    functions.append(func_data)
            elif node.type == 'classdef':
                class_data = self._extract_class(node)
                if class_data:
                    classes.append(class_data)
            elif node.type in ['import_name', 'import_from']:
                import_data = self._extract_import(node)
                if import_data:
                    imports.append(import_data)
            elif hasattr(node, 'get_error'):
                errors.append(str(node.get_error()))
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "packages": packages,
            "parseErrors": errors,
            "isPartialParse": len(errors) > 0
        }
    
    def _walk_tree(self, node):
        """Recursively walk through all nodes in the tree"""
        yield node
        if hasattr(node, 'children'):
            for child in node.children:
                yield from self._walk_tree(child)
    
    def _extract_function(self, node) -> Dict[str, Any]:
        try:
            name = node.children[1].value if len(node.children) > 1 else "unknown"
            
            # Extract parameters
            params = []
            try:
                # Find parameters node
                for child in node.children:
                    if child.type == 'parameters':
                        for param_child in child.children:
                            if hasattr(param_child, 'value') and param_child.type == 'name':
                                params.append(param_child.value)
            except:
                pass
            
            # Extract docstring
            docstring = None
            try:
                # Look for docstring in function body
                for child in node.children:
                    if child.type == 'suite':
                        for stmt in child.children:
                            if hasattr(stmt, 'children') and stmt.children:
                                first = stmt.children[0]
                                if hasattr(first, 'type') and first.type == 'string':
                                    docstring = first.value.strip('"\'')
                                    break
            except:
                pass
            
            return {
                "@type": "Function",
                "name": name,
                "parameters": params,
                "docstring": docstring,
                "startLine": node.start_pos[0],
                "endLine": node.end_pos[0],
                "text": node.get_code(),
                "isErrorRecovered": hasattr(node, 'get_error')
            }
        except Exception:
            return None
    
    def _extract_class(self, node) -> Dict[str, Any]:
        try:
            name = node.children[1].value if len(node.children) > 1 else "unknown"
            
            # Extract base classes
            bases = []
            try:
                for child in node.children:
                    if child.type == 'arglist':
                        for arg in child.children:
                            if hasattr(arg, 'value') and arg.type == 'name':
                                bases.append(arg.value)
            except:
                pass
            
            # Extract methods
            methods = []
            try:
                for child in node.children:
                    if child.type == 'suite':
                        for stmt_child in self._walk_tree(child):
                            if stmt_child.type == 'funcdef':
                                method_data = self._extract_function(stmt_child)
                                if method_data:
                                    method_data["@type"] = "Method"
                                    method_data["inClass"] = name
                                    methods.append(method_data)
            except:
                pass
            
            # Extract docstring
            docstring = None
            try:
                for child in node.children:
                    if child.type == 'suite':
                        for stmt in child.children:
                            if hasattr(stmt, 'children') and stmt.children:
                                first = stmt.children[0]
                                if hasattr(first, 'type') and first.type == 'string':
                                    docstring = first.value.strip('"\'')
                                    break
            except:
                pass
            
            return {
                "@type": "Class",
                "name": name,
                "bases": bases,
                "methods": methods,
                "docstring": docstring,
                "startLine": node.start_pos[0],
                "endLine": node.end_pos[0],
                "text": node.get_code(),
                "isErrorRecovered": hasattr(node, 'get_error')
            }
        except Exception:
            return None
    
    def _extract_import(self, node) -> Dict[str, Any]:
        """Extract import statements"""
        try:
            import_text = node.get_code().strip()
            
            if node.type == 'import_name':
                # Handle 'import module' statements
                modules = []
                for child in node.children:
                    if child.type == 'dotted_as_names':
                        for name_child in child.children:
                            if hasattr(name_child, 'value') and name_child.type == 'name':
                                modules.append(name_child.value)
                    elif child.type == 'dotted_name':
                        modules.append(child.get_code())
                    elif hasattr(child, 'value') and child.type == 'name':
                        modules.append(child.value)
                
                return {
                    "@type": "Import",
                    "modules": modules,
                    "text": import_text,
                    "startLine": node.start_pos[0]
                }
            
            elif node.type == 'import_from':
                # Handle 'from module import ...' statements
                module = ""
                names = []
                
                for child in node.children:
                    if child.type == 'dotted_name':
                        module = child.get_code()
                    elif child.type == 'name' and hasattr(child, 'value'):
                        # This might be the module name
                        if not module:
                            module = child.value
                    elif child.type == 'import_as_names':
                        for name_child in child.children:
                            if hasattr(name_child, 'value') and name_child.type == 'name':
                                names.append(name_child.value)
                    elif hasattr(child, 'value') and child.value == '*':
                        names = ["*"]
                
                return {
                    "@type": "ImportFrom",
                    "module": module,
                    "names": names,
                    "text": import_text,
                    "startLine": node.start_pos[0]
                }
            
        except Exception as e:
            return {
                "@type": "Import",
                "text": node.get_code().strip() if hasattr(node, 'get_code') else str(node),
                "error": str(e),
                "startLine": node.start_pos[0] if hasattr(node, 'start_pos') else 0
            }