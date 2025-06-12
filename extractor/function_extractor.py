import ast
import os
from .libcst_extractor import extract_with_libcst
from .parso_extractor import ParsoExtractor
from .type_analyzer import TypeAnalyzer
from .security_analyzer import SecurityAnalyzer
from .call_graph_extractor import CallGraphExtractor
from .data_flow_analyzer import DataFlowAnalyzer

class FunctionExtractor(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions_outside_classes = []

    def visit_ClassDef(self, node):
        class_entry = {"@type": "Class", "name": node.name, "hasPart": []}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                class_entry["hasPart"].append(
                    self.function_to_json(item, class_name=node.name)
                )
        self.classes.append(class_entry)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if not isinstance(getattr(node, "parent", None), ast.ClassDef):
            self.functions_outside_classes.append(self.function_to_json(node))

    def visit_AsyncFunctionDef(self, node):
        if not isinstance(getattr(node, "parent", None), ast.ClassDef):
            self.functions_outside_classes.append(
                self.function_to_json(node, is_async=True)
            )

    def function_to_json(self, node, class_name=None, is_async=False):
        # decorators
        decorators = []
        for dec in getattr(node, "decorator_list", []):
            if isinstance(dec, ast.Name): decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute): decorators.append(dec.attr)
            else: decorators.append(ast.get_source_segment(self.source, dec))
        # call graph
        calls = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Attribute): calls.append(n.func.attr)
                elif isinstance(n.func, ast.Name): calls.append(n.func.id)
        fn = {
            "@type": "Function",
            "name": node.name,
            "text": ast.get_source_segment(self.source, node),
            "description": ast.get_docstring(node) or "",
            "decorators": list(set(decorators)),
            "calls": list(set(calls)),
            "isAsync": is_async
        }
        if class_name: fn["inClass"] = class_name
        return fn

    def extract(self, code):
        self.source = code
        tree = ast.parse(code)
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node): child.parent = node
        self.visit(tree)
        return self.classes, self.functions_outside_classes

class EnhancedFunctionExtractor(FunctionExtractor):
    def __init__(self):
        super().__init__()
        self.parso_extractor = ParsoExtractor()
        self.type_analyzer = TypeAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        # NEW: Add relationship analyzers
        self.call_graph_extractor = CallGraphExtractor()
        self.data_flow_analyzer = DataFlowAnalyzer()

    def extract_enhanced(self, code, file_path=None, package_root=None):
        classes, functions = self.extract(code)
        libcst_data = extract_with_libcst(code)
        parso_data = self.parso_extractor.extract_with_error_recovery(code)
        
        # Fixed: Use package_root or file directory for analysis
        analysis_path = package_root or (os.path.dirname(file_path) if file_path else None)
        type_analysis = self.type_analyzer.analyze_types(analysis_path) if analysis_path else None
        security_analysis = self.security_analyzer.analyze_security(analysis_path) if analysis_path else None
        
        # NEW: Add semantic relationship analysis
        call_graph = self.call_graph_extractor.extract_call_relationships(code)
        data_flow = self.data_flow_analyzer.extract_data_flows(code)
        
        return {
            "ast": {"classes": classes, "functions": functions},
            "libcst": libcst_data,
            "parso": parso_data,
            "typeAnalysis": type_analysis,
            "securityAnalysis": security_analysis,
            # NEW: Semantic relationships for AI agents
            "callGraph": call_graph,
            "dataFlow": data_flow,
            "analysisPath": analysis_path  # For debugging
        }