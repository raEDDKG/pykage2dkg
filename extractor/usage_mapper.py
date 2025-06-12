"""
Usage Mapper for DKG Enhancement
Generates import-to-usage mappings for AI agents
"""

import ast
import inspect
import importlib
from typing import Dict, List, Any, Optional
import os

class UsageMapper:
    """Maps imports to usage patterns for AI agents"""
    
    def __init__(self):
        self.usage_patterns = {}
        self.import_mappings = {}
        self.working_examples = {}
    
    def analyze_package_usage(self, package_path: str, package_name: str) -> Dict[str, Any]:
        """Analyze package for AI agent usage patterns"""
        
        usage_data = {
            "importMappings": {},
            "workingExamples": {},
            "commonErrors": {},
            "primaryAPI": {},
            "quickStart": []
        }
        
        # Find all modules in package
        modules = self._find_modules(package_path)
        
        for module_path in modules:
            module_usage = self._analyze_module_usage(module_path, package_name)
            usage_data["importMappings"].update(module_usage.get("imports", {}))
            usage_data["workingExamples"].update(module_usage.get("examples", {}))
        
        # Generate quick start guide
        usage_data["quickStart"] = self._generate_quick_start(package_name, usage_data)
        
        return usage_data
    
    def _find_modules(self, package_path: str) -> List[str]:
        """Find all Python modules in package"""
        modules = []
        for root, dirs, files in os.walk(package_path):
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            for file in files:
                if file.endswith('.py'):
                    modules.append(os.path.join(root, file))
        return modules
    
    def _analyze_module_usage(self, module_path: str, package_name: str) -> Dict[str, Any]:
        """Analyze individual module for usage patterns"""
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Extract functions and classes
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):  # Skip private classes
                        classes.append(node.name)
            
            # Generate import mappings
            module_name = self._get_module_name(module_path, package_name)
            import_mappings = {}
            examples = {}
            
            for func in functions:
                import_mappings[func] = {
                    "primary": f"from {module_name} import {func}",
                    "alternative": f"import {package_name}; {package_name}.{func}(...)",
                    "packageLevel": f"import {package_name}" if module_name == package_name else f"from {package_name} import {func}"
                }
                
                # Generate basic usage example
                examples[func] = {
                    "basicUsage": f"{func}(...)",
                    "withImport": f"from {module_name} import {func}\nresult = {func}(...)"
                }
            
            for cls in classes:
                import_mappings[cls] = {
                    "primary": f"from {module_name} import {cls}",
                    "alternative": f"import {package_name}; {package_name}.{cls}(...)",
                    "packageLevel": f"import {package_name}" if module_name == package_name else f"from {package_name} import {cls}"
                }
                
                examples[cls] = {
                    "basicUsage": f"instance = {cls}(...)",
                    "withImport": f"from {module_name} import {cls}\ninstance = {cls}(...)"
                }
            
            return {
                "imports": import_mappings,
                "examples": examples
            }
            
        except Exception as e:
            print(f"Warning: Could not analyze {module_path}: {e}")
            return {"imports": {}, "examples": {}}
    
    def _get_module_name(self, module_path: str, package_name: str) -> str:
        """Convert file path to module name"""
        # This is a simplified version - would need more robust path handling
        if module_path.endswith('__init__.py'):
            return package_name
        else:
            filename = os.path.basename(module_path).replace('.py', '')
            return f"{package_name}.{filename}"
    
    def _generate_quick_start(self, package_name: str, usage_data: Dict[str, Any]) -> List[str]:
        """Generate quick start guide for the package"""
        
        quick_start = [
            f"# Quick Start Guide for {package_name}",
            f"import {package_name}",
            "",
            "# Common usage patterns:"
        ]
        
        # Add examples for first few functions
        examples = usage_data.get("workingExamples", {})
        for i, (func_name, example) in enumerate(examples.items()):
            if i >= 3:  # Limit to first 3 examples
                break
            quick_start.append(f"# {func_name}")
            quick_start.append(example.get("withImport", f"{func_name}(...)"))
            quick_start.append("")
        
        return quick_start

def enhance_with_usage_mapping(jsonld_data: Dict[str, Any], package_path: str, package_name: str) -> Dict[str, Any]:
    """Enhance JSON-LD with usage mapping for AI agents"""
    
    mapper = UsageMapper()
    usage_data = mapper.analyze_package_usage(package_path, package_name)
    
    # Add usage data to JSON-LD
    if "aiAgentGuidance" not in jsonld_data:
        jsonld_data["aiAgentGuidance"] = {}
    
    jsonld_data["aiAgentGuidance"].update({
        "@type": "AIAgentGuidance",
        "importMappings": usage_data["importMappings"],
        "workingExamples": usage_data["workingExamples"],
        "quickStart": usage_data["quickStart"],
        "generatedFor": "DKG_AI_Agent_Usage"
    })
    
    return jsonld_data