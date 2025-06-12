"""
Enhanced Import Validator - Fixed for Virtual Environment Usage

This version properly handles:
1. Virtual environment import validation
2. Clean module name generation
3. Concise, actionable AI agent guidance
4. Practical import patterns vs verbose errors
"""

import ast
import importlib
import inspect
import os
import sys
import subprocess
from typing import Dict, List, Any, Optional, Tuple
import warnings
import tempfile
import json

class EnhancedImportValidator:
    """Enhanced import validator that works properly in virtual environments"""
    
    def __init__(self, python_executable: Optional[str] = None):
        self.python_executable = python_executable or sys.executable
        self.validated_imports = {}
        self.failed_imports = {}
        self.available_exports = {}
        
    def validate_package_imports_in_venv(self, package_path: str, package_name: str, 
                                        python_executable: str) -> Dict[str, Any]:
        """
        Validate imports by running validation in the target Python environment
        This ensures we test imports in the correct virtual environment
        """
        
        # Create a validation script
        validation_script = self._create_validation_script(package_path, package_name)
        
        try:
            # Run the validation script in the target environment
            result = subprocess.run([
                python_executable, '-c', validation_script
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Parse the JSON output
                validation_data = json.loads(result.stdout)
                return self._process_validation_results(validation_data, package_name)
            else:
                return {
                    "validatedImports": {},
                    "failedImports": {"validation_error": result.stderr},
                    "aiAgentGuidance": {
                        "status": "validation_failed",
                        "error": result.stderr
                    }
                }
                
        except Exception as e:
            return {
                "validatedImports": {},
                "failedImports": {"exception": str(e)},
                "aiAgentGuidance": {
                    "status": "validation_exception",
                    "error": str(e)
                }
            }
    
    def _create_validation_script(self, package_path: str, package_name: str) -> str:
        """Create a Python script that validates imports and returns JSON"""
        
        script = f'''
import json
import importlib
import inspect
import warnings
import sys
import os

def validate_package_imports():
    """Validate imports for package: {package_name}"""
    
    results = {{
        "validatedImports": {{}},
        "failedImports": {{}},
        "availableExports": {{}},
        "packageInfo": {{}}
    }}
    
    # Test basic package import
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            package = importlib.import_module("{package_name}")
        
        results["packageInfo"] = {{
            "name": "{package_name}",
            "file": getattr(package, "__file__", "unknown"),
            "version": getattr(package, "__version__", "unknown")
        }}
        
        # Get available exports
        exports = []
        if hasattr(package, "__all__"):
            exports = list(package.__all__)
        else:
            # Get public attributes
            for name in dir(package):
                if not name.startswith("_"):
                    try:
                        attr = getattr(package, name)
                        if (inspect.isfunction(attr) or inspect.isclass(attr) or 
                            inspect.ismodule(attr) or callable(attr)):
                            exports.append(name)
                    except:
                        pass
        
        results["availableExports"]["{package_name}"] = exports
        
        # Test individual imports
        for export_name in exports[:20]:  # Limit to first 20 for performance
            import_statement = f"from {package_name} import {{export_name}}"
            try:
                namespace = {{}}
                exec(import_statement, namespace)
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
                    
                    results["validatedImports"][f"{package_name}.{{export_name}}"] = {{
                        "importPath": import_statement,
                        "exportType": item_type,
                        "verified": True
                    }}
            except Exception as e:
                results["failedImports"][f"{package_name}.{{export_name}}"] = {{
                    "importPath": import_statement,
                    "error": str(e),
                    "verified": False
                }}
        
        # Test common submodule patterns
        common_submodules = ["core", "main", "api", "client", "utils", "helpers"]
        for submodule in common_submodules:
            try:
                submodule_name = f"{package_name}.{{submodule}}"
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sub_mod = importlib.import_module(submodule_name)
                
                results["validatedImports"][submodule_name] = {{
                    "importPath": f"import {{submodule_name}}",
                    "exportType": "module",
                    "verified": True
                }}
            except ImportError:
                pass  # Submodule doesn't exist, which is fine
            except Exception as e:
                results["failedImports"][submodule_name] = {{
                    "importPath": f"import {{submodule_name}}",
                    "error": str(e),
                    "verified": False
                }}
                
    except ImportError as e:
        results["failedImports"]["{package_name}"] = {{
            "importPath": "import {package_name}",
            "error": str(e),
            "verified": False
        }}
    except Exception as e:
        results["failedImports"]["{package_name}"] = {{
            "importPath": "import {package_name}",
            "error": f"Unexpected error: {{str(e)}}",
            "verified": False
        }}
    
    return results

# Run validation and output JSON
if __name__ == "__main__":
    try:
        results = validate_package_imports()
        print(json.dumps(results, indent=2))
    except Exception as e:
        error_result = {{
            "validatedImports": {{}},
            "failedImports": {{"script_error": str(e)}},
            "availableExports": {{}},
            "packageInfo": {{}}
        }}
        print(json.dumps(error_result, indent=2))
'''
        return script
    
    def _process_validation_results(self, validation_data: Dict[str, Any], package_name: str) -> Dict[str, Any]:
        """Process validation results and create AI agent guidance"""
        
        validated_imports = validation_data.get("validatedImports", {})
        failed_imports = validation_data.get("failedImports", {})
        available_exports = validation_data.get("availableExports", {})
        
        # Create concise AI agent guidance
        ai_guidance = self._create_ai_agent_guidance(
            validated_imports, failed_imports, available_exports, package_name
        )
        
        return {
            "validatedImports": validated_imports,
            "failedImports": failed_imports,
            "availableExports": available_exports,
            "aiAgentGuidance": ai_guidance
        }
    
    def _create_ai_agent_guidance(self, validated_imports: Dict[str, Any], 
                                 failed_imports: Dict[str, Any], 
                                 available_exports: Dict[str, Any],
                                 package_name: str) -> Dict[str, Any]:
        """Create concise, actionable AI agent guidance"""
        
        # Extract safe import patterns
        safe_imports = []
        import_patterns = {
            "basic": [],
            "specific": [],
            "classes": [],
            "functions": []
        }
        
        for import_key, import_info in validated_imports.items():
            import_path = import_info.get("importPath", "")
            export_type = import_info.get("exportType", "unknown")
            
            safe_imports.append(import_path)
            
            # Categorize imports
            if import_path.startswith(f"import {package_name}"):
                import_patterns["basic"].append(import_path)
            elif export_type == "class":
                import_patterns["classes"].append(import_path)
            elif export_type == "function":
                import_patterns["functions"].append(import_path)
            else:
                import_patterns["specific"].append(import_path)
        
        # Create practical recommendations
        recommendations = []
        if import_patterns["basic"]:
            recommendations.append(f"Use basic import: import {package_name}")
        if import_patterns["functions"]:
            recommendations.append("Import specific functions for better performance")
        if import_patterns["classes"]:
            recommendations.append("Import classes directly when needed")
        
        # Identify common failure patterns
        failure_patterns = []
        for import_key, import_info in failed_imports.items():
            error = import_info.get("error", "")
            if "No module named" in error:
                failure_patterns.append("Module not available in this environment")
            elif "cannot import name" in error:
                failure_patterns.append("Export not available from module")
        
        return {
            "@type": "AIAgentImportGuidance",
            "packageName": package_name,
            "status": "success" if validated_imports else "limited",
            "safeImports": safe_imports[:10],  # Top 10 safe imports
            "importPatterns": {
                "recommended": import_patterns["basic"][:3],
                "specific": import_patterns["specific"][:5],
                "classes": import_patterns["classes"][:5],
                "functions": import_patterns["functions"][:5]
            },
            "recommendations": recommendations,
            "commonFailures": list(set(failure_patterns)),
            "summary": {
                "totalValidated": len(validated_imports),
                "totalFailed": len(failed_imports),
                "availableExports": len(available_exports.get(package_name, []))
            }
        }

def enhance_with_enhanced_import_validation(metadata: Dict[str, Any], package_path: str, 
                                          package_name: str, python_executable: str) -> Dict[str, Any]:
    """
    Enhanced version of import validation enhancement
    """
    
    validator = EnhancedImportValidator(python_executable)
    
    try:
        validation_results = validator.validate_package_imports_in_venv(
            package_path, package_name, python_executable
        )
        
        # Add to metadata
        metadata["importValidation"] = validation_results
        
        # Add summary to analysis metadata
        if "analysisMetadata" not in metadata:
            metadata["analysisMetadata"] = {}
        
        metadata["analysisMetadata"]["importValidation"] = {
            "tool": "enhanced_import_validator",
            "approach": "virtual_environment_validation",
            "validatedImports": len(validation_results.get("validatedImports", {})),
            "failedImports": len(validation_results.get("failedImports", {})),
            "status": validation_results.get("aiAgentGuidance", {}).get("status", "unknown")
        }
        
        return metadata
        
    except Exception as e:
        # Graceful fallback
        metadata["importValidation"] = {
            "validatedImports": {},
            "failedImports": {"enhancement_error": str(e)},
            "aiAgentGuidance": {
                "status": "enhancement_failed",
                "error": str(e),
                "fallback": "Basic import analysis may be available"
            }
        }
        
        return metadata