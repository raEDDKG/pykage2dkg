# extractor/treesitter_extractor.py
try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjs
    import tree_sitter_typescript as tsts
    from tree_sitter import Language, Parser, Node
    TREE_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Tree-sitter not available: {e}")
    TREE_SITTER_AVAILABLE = False

from typing import Dict, List, Any, Optional
import os

class TreeSitterExtractor:
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            self.languages = {}
            self.parser = None
            return
            
        try:
            self.languages = {
                'python': Language(tspython.language()),
            }
            
            # Try to add JavaScript support
            try:
                self.languages['javascript'] = Language(tsjs.language())
            except Exception as e:
                print(f"Warning: JavaScript tree-sitter not available: {e}")
            
            # Try to add TypeScript support
            try:
                # Different tree-sitter-typescript versions have different APIs
                if hasattr(tsts, 'language'):
                    self.languages['typescript'] = Language(tsts.language())
                elif hasattr(tsts, 'language_typescript'):
                    self.languages['typescript'] = Language(tsts.language_typescript())
                else:
                    print("Warning: TypeScript tree-sitter language function not found")
            except Exception as e:
                print(f"Warning: TypeScript tree-sitter not available: {e}")
                
            self.parser = Parser()
        except Exception as e:
            print(f"Warning: Failed to initialize tree-sitter: {e}")
            self.languages = {}
            self.parser = None
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract from file based on extension"""
        if not TREE_SITTER_AVAILABLE or self.parser is None:
            return {
                "@type": "CrossLanguageCodeFile",
                "error": "Tree-sitter not available",
                "language": "unknown",
                "functions": [],
                "classes": [],
                "imports": [],
                "exports": []
            }
            
        ext = os.path.splitext(file_path)[1].lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }
        
        language = lang_map.get(ext, 'python')
        
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            return self.extract(source_code, language)
        except Exception as e:
            return {"error": str(e), "language": language}
    
    def extract(self, source_code: bytes, language: str = 'python') -> Dict[str, Any]:
        """Extract structure using Tree-sitter"""
        if not TREE_SITTER_AVAILABLE or self.parser is None:
            return {
                "@type": "CrossLanguageCodeFile",
                "error": "Tree-sitter not available",
                "language": language,
                "functions": [],
                "classes": [],
                "imports": [],
                "exports": []
            }
            
        if language not in self.languages:
            return {"error": f"Unsupported language: {language}"}
        
        self.parser.set_language(self.languages[language])
        tree = self.parser.parse(source_code)
        
        return {
            "@type": "CrossLanguageCodeFile",
            "language": language,
            "functions": self._extract_functions(tree.root_node, source_code),
            "classes": self._extract_classes(tree.root_node, source_code),
            "imports": self._extract_imports(tree.root_node, source_code),
            "exports": self._extract_exports(tree.root_node, source_code) if language in ['javascript', 'typescript'] else []
        }
    
    def _extract_functions(self, node: Node, source: bytes) -> List[Dict[str, Any]]:
        functions = []
        
        def traverse(n):
            if n.type in ['function_definition', 'function_declaration', 'method_definition']:
                func_data = {
                    "@type": "Function",
                    "name": self._get_function_name(n, source),
                    "startByte": n.start_byte,
                    "endByte": n.end_byte,
                    "startPoint": {"row": n.start_point[0], "column": n.start_point[1]},
                    "endPoint": {"row": n.end_point[0], "column": n.end_point[1]},
                    "text": source[n.start_byte:n.end_byte].decode('utf-8', errors='ignore')
                }
                functions.append(func_data)
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return functions
    
    def _extract_classes(self, node: Node, source: bytes) -> List[Dict[str, Any]]:
        classes = []
        
        def traverse(n):
            if n.type in ['class_definition', 'class_declaration']:
                class_data = {
                    "@type": "Class", 
                    "name": self._get_class_name(n, source),
                    "startByte": n.start_byte,
                    "endByte": n.end_byte,
                    "methods": []
                }
                
                # Extract methods within class
                for child in n.children:
                    if child.type in ['function_definition', 'method_definition']:
                        method_data = {
                            "@type": "Method",
                            "name": self._get_function_name(child, source),
                            "text": source[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
                        }
                        class_data["methods"].append(method_data)
                
                classes.append(class_data)
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return classes
    
    def _extract_imports(self, node: Node, source: bytes) -> List[Dict[str, Any]]:
        imports = []
        
        def traverse(n):
            if n.type in ['import_statement', 'import_from_statement', 'import_declaration']:
                import_data = {
                    "@type": "Import",
                    "text": source[n.start_byte:n.end_byte].decode('utf-8', errors='ignore').strip(),
                    "startLine": n.start_point[0] + 1
                }
                imports.append(import_data)
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return imports
    
    def _extract_exports(self, node: Node, source: bytes) -> List[Dict[str, Any]]:
        exports = []
        
        def traverse(n):
            if n.type in ['export_statement', 'export_declaration']:
                export_data = {
                    "@type": "Export",
                    "text": source[n.start_byte:n.end_byte].decode('utf-8', errors='ignore').strip(),
                    "startLine": n.start_point[0] + 1
                }
                exports.append(export_data)
            
            for child in n.children:
                traverse(child)
        
        traverse(node)
        return exports
    
    def _get_function_name(self, node: Node, source: bytes) -> str:
        for child in node.children:
            if child.type == 'identifier':
                return source[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
        return "unknown"
    
    def _get_class_name(self, node: Node, source: bytes) -> str:
        for child in node.children:
            if child.type == 'identifier':
                return source[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
        return "unknown"