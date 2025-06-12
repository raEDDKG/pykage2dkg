# extractor/call_graph_extractor.py
import ast
from typing import Dict, List, Set, Any
from collections import defaultdict

class CallGraphExtractor(ast.NodeVisitor):
    """Extract function call relationships for AI agent understanding"""
    
    def __init__(self):
        self.call_graph = defaultdict(set)  # caller -> set of callees
        self.current_function = None
        self.current_class = None
        self.function_definitions = {}  # name -> node info
        self.class_definitions = {}    # name -> node info
        self.call_details = []         # detailed call information
        
    def visit_ClassDef(self, node):
        """Track class context for method calls"""
        old_class = self.current_class
        self.current_class = node.name
        
        self.class_definitions[node.name] = {
            "name": node.name,
            "methods": [],
            "line": node.lineno
        }
        
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Track function definitions and their calls"""
        function_name = self._get_qualified_name(node.name)
        
        self.function_definitions[function_name] = {
            "name": node.name,
            "qualifiedName": function_name,
            "class": self.current_class,
            "line": node.lineno,
            "parameters": [arg.arg for arg in node.args.args],
            "isAsync": False
        }
        
        # Add to class methods if in a class
        if self.current_class:
            self.class_definitions[self.current_class]["methods"].append(function_name)
        
        old_function = self.current_function
        self.current_function = function_name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Track async function definitions"""
        function_name = self._get_qualified_name(node.name)
        
        self.function_definitions[function_name] = {
            "name": node.name,
            "qualifiedName": function_name,
            "class": self.current_class,
            "line": node.lineno,
            "parameters": [arg.arg for arg in node.args.args],
            "isAsync": True
        }
        
        if self.current_class:
            self.class_definitions[self.current_class]["methods"].append(function_name)
        
        old_function = self.current_function
        self.current_function = function_name
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_Call(self, node):
        """Track function calls and build call graph"""
        if self.current_function:
            callee_info = self._extract_call_info(node)
            if callee_info:
                callee_name = callee_info["name"]
                self.call_graph[self.current_function].add(callee_name)
                
                # Store detailed call information
                self.call_details.append({
                    "caller": self.current_function,
                    "callee": callee_name,
                    "calleeType": callee_info["type"],
                    "line": node.lineno,
                    "argumentCount": len(node.args),
                    "hasKeywordArgs": len(node.keywords) > 0,
                    "context": self.current_class
                })
        
        self.generic_visit(node)
    
    def _get_qualified_name(self, name: str) -> str:
        """Get qualified name including class context"""
        if self.current_class:
            return f"{self.current_class}.{name}"
        return name
    
    def _extract_call_info(self, node) -> Dict[str, str]:
        """Extract information about a function call"""
        if isinstance(node.func, ast.Name):
            return {
                "name": node.func.id,
                "type": "function"
            }
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                return {
                    "name": f"{node.func.value.id}.{node.func.attr}",
                    "type": "method"
                }
            else:
                return {
                    "name": node.func.attr,
                    "type": "attribute_call"
                }
        elif isinstance(node.func, ast.Call):
            # Handle complex calls like func()()
            return {
                "name": "complex_call",
                "type": "chained_call"
            }
        return None
    
    def extract_call_relationships(self, code: str) -> Dict[str, Any]:
        """Extract complete call graph from code"""
        try:
            tree = ast.parse(code)
            self.visit(tree)
            
            # Build relationship summary
            relationships = []
            for caller, callees in self.call_graph.items():
                relationships.append({
                    "@type": "FunctionCall",
                    "caller": caller,
                    "callees": list(callees),
                    "callCount": len(callees),
                    "uniqueCallees": len(callees)
                })
            
            # Analyze call patterns
            call_patterns = self._analyze_call_patterns()
            
            return {
                "@type": "CallGraph",
                "relationships": relationships,
                "callDetails": self.call_details,
                "functions": list(self.function_definitions.keys()),
                "classes": list(self.class_definitions.keys()),
                "totalRelationships": sum(len(callees) for callees in self.call_graph.values()),
                "callPatterns": call_patterns,
                "extractionStatus": "success"
            }
            
        except Exception as e:
            return {
                "@type": "CallGraph",
                "relationships": [],
                "callDetails": [],
                "functions": [],
                "classes": [],
                "totalRelationships": 0,
                "callPatterns": {},
                "error": str(e),
                "extractionStatus": "failed"
            }
    
    def _analyze_call_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in function calls for AI insights"""
        patterns = {
            "mostCalledFunctions": {},
            "mostCallingFunctions": {},
            "recursiveFunctions": [],
            "isolatedFunctions": [],
            "callDepth": {}
        }
        
        # Count how often each function is called
        call_counts = defaultdict(int)
        for details in self.call_details:
            call_counts[details["callee"]] += 1
        
        # Most called functions
        patterns["mostCalledFunctions"] = dict(
            sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Functions that make the most calls
        caller_counts = {caller: len(callees) for caller, callees in self.call_graph.items()}
        patterns["mostCallingFunctions"] = dict(
            sorted(caller_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Detect recursive functions
        for caller, callees in self.call_graph.items():
            if caller in callees:
                patterns["recursiveFunctions"].append(caller)
        
        # Find isolated functions (defined but never called)
        all_called = set()
        for callees in self.call_graph.values():
            all_called.update(callees)
        
        patterns["isolatedFunctions"] = [
            func for func in self.function_definitions.keys() 
            if func not in all_called
        ]
        
        return patterns


def extract_call_graph(source_code: str) -> Dict[str, Any]:
    """Convenience function to extract call graph from source code"""
    extractor = CallGraphExtractor()
    return extractor.extract_call_relationships(source_code)