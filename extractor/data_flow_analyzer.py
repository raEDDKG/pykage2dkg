# extractor/data_flow_analyzer.py
import ast
from typing import Dict, List, Any, Set
from collections import defaultdict

class DataFlowAnalyzer(ast.NodeVisitor):
    """Analyze data flow patterns for AI agent understanding"""
    
    def __init__(self):
        self.data_flows = []
        self.current_function = None
        self.current_class = None
        self.variables = {}  # var_name -> definition_info
        self.function_variables = defaultdict(dict)  # function -> {var -> info}
        self.data_dependencies = defaultdict(set)  # var -> set of vars it depends on
        
    def visit_ClassDef(self, node):
        """Track class context"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Track function context and parameters"""
        function_name = self._get_qualified_name(node.name)
        old_function = self.current_function
        self.current_function = function_name
        
        # Track parameters as input data
        for arg in node.args.args:
            var_info = {
                "type": "parameter",
                "function": function_name,
                "source": "input",
                "line": node.lineno,
                "dataType": self._extract_type_annotation(arg.annotation)
            }
            self.function_variables[function_name][arg.arg] = var_info
            
            # Record data flow for parameters
            self.data_flows.append({
                "@type": "DataFlow",
                "function": function_name,
                "variable": arg.arg,
                "flowType": "parameter_input",
                "source": "function_parameter",
                "destination": arg.arg,
                "line": node.lineno
            })
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions"""
        self.visit_FunctionDef(node)
    
    def visit_Assign(self, node):
        """Track variable assignments and data flow"""
        if self.current_function:
            # Analyze the value being assigned
            value_source = self._analyze_value_source(node.value)
            
            # Track assignments to variables
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    
                    # Store variable information
                    var_info = {
                        "type": "assignment",
                        "function": self.current_function,
                        "source": value_source,
                        "line": node.lineno
                    }
                    self.function_variables[self.current_function][var_name] = var_info
                    
                    # Record data flow
                    self.data_flows.append({
                        "@type": "DataFlow",
                        "function": self.current_function,
                        "variable": var_name,
                        "flowType": "assignment",
                        "source": value_source,
                        "destination": var_name,
                        "line": node.lineno
                    })
                    
                    # Track data dependencies
                    if value_source.get("type") == "variable":
                        source_var = value_source.get("name")
                        if source_var:
                            self.data_dependencies[var_name].add(source_var)
                    elif value_source.get("type") == "function_call":
                        # Variable depends on function call result
                        func_name = value_source.get("function")
                        if func_name:
                            self.data_dependencies[var_name].add(f"call:{func_name}")
        
        self.generic_visit(node)
    
    def visit_AugAssign(self, node):
        """Track augmented assignments (+=, -=, etc.)"""
        if self.current_function and isinstance(node.target, ast.Name):
            var_name = node.target.id
            value_source = self._analyze_value_source(node.value)
            
            self.data_flows.append({
                "@type": "DataFlow",
                "function": self.current_function,
                "variable": var_name,
                "flowType": "augmented_assignment",
                "operation": type(node.op).__name__,
                "source": value_source,
                "destination": var_name,
                "line": node.lineno
            })
            
            # Variable depends on itself and the new value
            self.data_dependencies[var_name].add(var_name)
            if value_source.get("type") == "variable":
                source_var = value_source.get("name")
                if source_var:
                    self.data_dependencies[var_name].add(source_var)
        
        self.generic_visit(node)
    
    def visit_Return(self, node):
        """Track return statements and output data flow"""
        if self.current_function and node.value:
            return_source = self._analyze_value_source(node.value)
            
            self.data_flows.append({
                "@type": "DataFlow",
                "function": self.current_function,
                "flowType": "return",
                "source": return_source,
                "destination": "function_output",
                "line": node.lineno
            })
        
        self.generic_visit(node)
    
    def visit_Yield(self, node):
        """Track yield statements (generators)"""
        if self.current_function and node.value:
            yield_source = self._analyze_value_source(node.value)
            
            self.data_flows.append({
                "@type": "DataFlow",
                "function": self.current_function,
                "flowType": "yield",
                "source": yield_source,
                "destination": "generator_output",
                "line": node.lineno
            })
        
        self.generic_visit(node)
    
    def _get_qualified_name(self, name: str) -> str:
        """Get qualified name including class context"""
        if self.current_class:
            return f"{self.current_class}.{name}"
        return name
    
    def _analyze_value_source(self, node) -> Dict[str, Any]:
        """Analyze where a value comes from"""
        if isinstance(node, ast.Name):
            return {
                "type": "variable",
                "name": node.id,
                "context": "local"
            }
        elif isinstance(node, ast.Call):
            return {
                "type": "function_call",
                "function": self._extract_call_name(node),
                "argumentCount": len(node.args)
            }
        elif isinstance(node, ast.Constant):
            return {
                "type": "constant",
                "value": str(node.value)[:50],  # Truncate long constants
                "valueType": type(node.value).__name__
            }
        elif isinstance(node, ast.List):
            return {
                "type": "list_literal",
                "elementCount": len(node.elts),
                "elements": [self._analyze_value_source(elt) for elt in node.elts[:3]]  # First 3 elements
            }
        elif isinstance(node, ast.Dict):
            return {
                "type": "dict_literal",
                "keyCount": len(node.keys)
            }
        elif isinstance(node, ast.BinOp):
            return {
                "type": "binary_operation",
                "operation": type(node.op).__name__,
                "left": self._analyze_value_source(node.left),
                "right": self._analyze_value_source(node.right)
            }
        elif isinstance(node, ast.Attribute):
            return {
                "type": "attribute_access",
                "object": self._analyze_value_source(node.value),
                "attribute": node.attr
            }
        else:
            return {
                "type": "expression",
                "nodeType": type(node).__name__
            }
    
    def _extract_call_name(self, node):
        """Extract function name from call node"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        else:
            return "unknown_call"
    
    def _extract_type_annotation(self, annotation):
        """Extract type annotation if present"""
        if annotation is None:
            return None
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        else:
            return type(annotation).__name__
    
    def extract_data_flows(self, code: str) -> Dict[str, Any]:
        """Extract complete data flow analysis from code"""
        try:
            tree = ast.parse(code)
            self.visit(tree)
            
            # Analyze data flow patterns
            flow_patterns = self._analyze_flow_patterns()
            
            return {
                "@type": "DataFlowAnalysis",
                "flows": self.data_flows,
                "functionVariables": dict(self.function_variables),
                "dataDependencies": {k: list(v) for k, v in self.data_dependencies.items()},
                "flowPatterns": flow_patterns,
                "totalFlows": len(self.data_flows),
                "extractionStatus": "success"
            }
            
        except Exception as e:
            return {
                "@type": "DataFlowAnalysis",
                "flows": [],
                "functionVariables": {},
                "dataDependencies": {},
                "flowPatterns": {},
                "totalFlows": 0,
                "error": str(e),
                "extractionStatus": "failed"
            }
    
    def _analyze_flow_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in data flow for AI insights"""
        patterns = {
            "inputOutputFunctions": {},
            "dataTransformers": [],
            "variableLifecycles": {},
            "complexDependencies": []
        }
        
        # Analyze input/output patterns per function
        for func_name, variables in self.function_variables.items():
            inputs = [var for var, info in variables.items() if info["type"] == "parameter"]
            outputs = []
            
            # Find outputs (returns)
            for flow in self.data_flows:
                if flow["function"] == func_name and flow["flowType"] == "return":
                    outputs.append(flow["source"])
            
            patterns["inputOutputFunctions"][func_name] = {
                "inputs": inputs,
                "outputs": outputs,
                "inputCount": len(inputs),
                "outputCount": len(outputs)
            }
        
        # Find data transformers (functions that modify data)
        for func_name, variables in self.function_variables.items():
            transformations = 0
            for var, info in variables.items():
                if info["type"] == "assignment" and info["source"].get("type") == "function_call":
                    transformations += 1
            
            if transformations > 0:
                patterns["dataTransformers"].append({
                    "function": func_name,
                    "transformationCount": transformations
                })
        
        # Analyze variable lifecycles
        for var, deps in self.data_dependencies.items():
            if len(deps) > 2:  # Complex dependencies
                patterns["complexDependencies"].append({
                    "variable": var,
                    "dependencies": list(deps),
                    "dependencyCount": len(deps)
                })
        
        return patterns


def extract_data_flow(source_code: str) -> Dict[str, Any]:
    """Convenience function to extract data flow from source code"""
    analyzer = DataFlowAnalyzer()
    return analyzer.extract_data_flows(source_code)