"""
Import Validator - Tests actual import availability
Solves the real problem: file structure ≠ import reality
"""

import ast
import importlib
import inspect
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import warnings

class ImportValidator:
    """Validates actual import availability vs. theoretical file structure"""
    
    def __init__(self):
        self.validated_imports = {}
        self.failed_imports = {}
        self.available_exports = {}
        
    def validate_package_imports(self, package_path: str, package_name: str) -> Dict[str, Any]:
        """Validate all possible imports for a package"""
        
        validation_results = {
            "validImports": {},
            "failedImports": {},
            "availableExports": {},
            "importGuidance": {},
            "realStructure": {}
        }
        
        # Find all Python modules
        modules = self._find_modules(package_path)
        
        for module_path in modules:
            module_name = self._get_module_name(module_path, package_name)
            
            # Test if module can be imported
            module_result = self._validate_module_import(module_name)
            
            if module_result["success"]:
                # Get actual exports from the module
                exports = self._get_actual_exports(module_name)
                validation_results["availableExports"][module_name] = exports
                
                # Test individual function/class imports
                for export_name in exports:
                    import_path = f"from {module_name} import {export_name}"
                    import_result = self._test_import(import_path, module_name, export_name)
                    
                    if import_result["success"]:
                        validation_results["validImports"][f"{module_name}.{export_name}"] = {
                            "importPath": import_path,
                            "alternative": f"import {module_name}; {module_name}.{export_name}",
                            "verified": True,
                            "exportType": import_result["type"]
                        }
                    else:
                        validation_results["failedImports"][f"{module_name}.{export_name}"] = {
                            "attemptedImport": import_path,
                            "error": import_result["error"],
                            "reason": import_result["reason"]
                        }
            else:
                validation_results["failedImports"][module_name] = {
                    "attemptedImport": f"import {module_name}",
                    "error": module_result["error"],
                    "reason": "Module not available"
                }
        
        # Generate AI agent guidance
        validation_results["importGuidance"] = self._generate_import_guidance(validation_results)
        
        return validation_results
    
    def _find_modules(self, package_path: str) -> List[str]:
        """Find all Python modules in package"""
        modules = []
        for root, dirs, files in os.walk(package_path):
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            for file in files:
                if file.endswith('.py'):
                    modules.append(os.path.join(root, file))
        return modules
    
    def _get_module_name(self, module_path: str, package_name: str) -> str:
        """Convert file path to module name - FIXED VERSION"""
        try:
            # Normalize the path
            module_path = os.path.normpath(module_path)
            
            # Find the package root by looking for the package name in the path
            path_parts = module_path.split(os.sep)
            
            # Find where the package name appears in the path
            package_index = -1
            for i, part in enumerate(path_parts):
                if part == package_name or part == package_name.replace('-', '_'):
                    package_index = i
                    break
            
            if package_index >= 0:
                # Get the relative path from the package root
                relative_parts = path_parts[package_index:]
                
                # Handle __init__.py files
                if relative_parts[-1] == '__init__.py':
                    if len(relative_parts) == 2:  # package/__init__.py
                        return package_name
                    else:  # package/submodule/__init__.py
                        module_parts = relative_parts[1:-1]  # Skip package name and __init__.py
                        return f"{package_name}.{'.'.join(module_parts)}"
                else:
                    # Handle regular .py files
                    filename = relative_parts[-1].replace('.py', '')
                    if len(relative_parts) == 2:  # package/module.py
                        return f"{package_name}.{filename}"
                    else:  # package/subpackage/module.py
                        module_parts = relative_parts[1:-1] + [filename]
                        return f"{package_name}.{'.'.join(module_parts)}"
            
            # Fallback: guess from filename
            filename = os.path.basename(module_path)
            if filename == '__init__.py':
                return package_name
            else:
                return f"{package_name}.{filename.replace('.py', '')}"
                
        except Exception as e:
            # Ultimate fallback
            filename = os.path.basename(module_path)
            if filename == '__init__.py':
                return package_name
            else:
                return f"{package_name}.{filename.replace('.py', '')}"
    
    def _validate_module_import(self, module_name: str) -> Dict[str, Any]:
        """Test if a module can actually be imported"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                module = importlib.import_module(module_name)
            return {
                "success": True,
                "module": module,
                "error": None
            }
        except ImportError as e:
            return {
                "success": False,
                "module": None,
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "module": None,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _get_actual_exports(self, module_name: str) -> List[str]:
        """Get what's actually available for import from a module"""
        try:
            module = importlib.import_module(module_name)
            
            # Check if module has __all__
            if hasattr(module, '__all__'):
                return list(module.__all__)
            
            # Otherwise, get public attributes
            exports = []
            for name in dir(module):
                if not name.startswith('_'):
                    attr = getattr(module, name)
                    # Include functions, classes, and other importable items
                    if (inspect.isfunction(attr) or 
                        inspect.isclass(attr) or 
                        inspect.ismodule(attr) or
                        callable(attr)):
                        exports.append(name)
            
            return exports
            
        except Exception as e:
            return []
    
    def _test_import(self, import_path: str, module_name: str, export_name: str) -> Dict[str, Any]:
        """Test if a specific import actually works"""
        try:
            # Create a temporary namespace to test the import
            namespace = {}
            exec(import_path, namespace)
            
            # Check if the import succeeded
            if export_name in namespace:
                imported_item = namespace[export_name]
                item_type = "unknown"
                
                if inspect.isfunction(imported_item):
                    item_type = "function"
                elif inspect.isclass(imported_item):
                    item_type = "class"
                elif inspect.ismodule(imported_item):
                    item_type = "module"
                elif callable(imported_item):
                    item_type = "callable"
                
                return {
                    "success": True,
                    "type": item_type,
                    "error": None,
                    "reason": None
                }
            else:
                return {
                    "success": False,
                    "type": None,
                    "error": f"{export_name} not found in namespace after import",
                    "reason": "Import succeeded but item not available"
                }
                
        except ImportError as e:
            return {
                "success": False,
                "type": None,
                "error": str(e),
                "reason": "Import failed"
            }
        except Exception as e:
            return {
                "success": False,
                "type": None,
                "error": str(e),
                "reason": "Unexpected error during import"
            }
    
    def _generate_import_guidance(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI agent guidance based on validation results"""
        
        guidance = {
            "safeImports": [],
            "unsafeImports": [],
            "recommendedPatterns": [],
            "commonErrors": []
        }
        
        # Safe imports
        for item_path, import_info in validation_results["validImports"].items():
            guidance["safeImports"].append({
                "item": item_path,
                "importStatement": import_info["importPath"],
                "alternative": import_info["alternative"],
                "type": import_info["exportType"],
                "verified": True
            })
        
        # Unsafe imports
        for item_path, error_info in validation_results["failedImports"].items():
            guidance["unsafeImports"].append({
                "item": item_path,
                "attemptedImport": error_info["attemptedImport"],
                "error": error_info["error"],
                "reason": error_info["reason"]
            })
        
        # Generate recommended patterns
        if guidance["safeImports"]:
            guidance["recommendedPatterns"] = [
                "# Verified working imports:",
                *[f"{imp['importStatement']}" for imp in guidance["safeImports"][:5]],
                "",
                "# These imports are verified to work in this environment"
            ]
        
        # Common error patterns
        error_patterns = {}
        for unsafe in guidance["unsafeImports"]:
            error = unsafe["error"]
            if "No module named" in error:
                error_patterns["missing_module"] = error_patterns.get("missing_module", 0) + 1
            elif "cannot import name" in error:
                error_patterns["missing_export"] = error_patterns.get("missing_export", 0) + 1
        
        guidance["commonErrors"] = [
            f"Missing modules: {error_patterns.get('missing_module', 0)} cases",
            f"Missing exports: {error_patterns.get('missing_export', 0)} cases"
        ]
        
        return guidance

def enhance_with_import_validation(jsonld_data: Dict[str, Any], package_path: str, package_name: str) -> Dict[str, Any]:
    """Enhance JSON-LD with real import validation"""
    
    validator = ImportValidator()
    validation_results = validator.validate_package_imports(package_path, package_name)
    
    # Add validation data to JSON-LD
    if "importValidation" not in jsonld_data:
        jsonld_data["importValidation"] = {}
    
    jsonld_data["importValidation"] = {
        "@type": "ImportValidation",
        "validatedImports": validation_results["validImports"],
        "failedImports": validation_results["failedImports"],
        "availableExports": validation_results["availableExports"],
        "aiAgentGuidance": validation_results["importGuidance"],
        "validationTimestamp": "2025-06-11T19:30:00Z",
        "environment": {
            "pythonVersion": sys.version,
            "platform": sys.platform
        }
    }
    
    return jsonld_data