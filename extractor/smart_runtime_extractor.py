#!/usr/bin/env python3

"""
Smart Runtime Behavior Extractor with improved test generation.

This module creates more intelligent tests that:
1. Import only functions and classes defined in the target module
2. Filter to only call things that are defined in your module
3. Skip anything that requires arguments (but allow optional arguments)
4. Instantiate classes with no-arg or all-optional-arg constructors
"""

import os
import sys
import json
import subprocess
import tempfile
import inspect
import ast
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path


class SmartRuntimeBehaviorExtractor:
    """Enhanced runtime behavior extractor with intelligent test generation"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='smart_runtime_analysis_')
        self.package_path = None
        
    def extract_runtime_behavior(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """Extract runtime behavior using smart test generation"""
        self.package_path = os.path.abspath(package_path)
        
        runtime_data = {
            "@type": "SmartRuntimeBehavior",
            "package_path": self.package_path,
            "test_generation": "smart_introspection",
            "executions": self.run_smart_tests(package_path, test_scripts),
            "summary": self.generate_execution_summary()
        }
        
        return runtime_data
    
    def run_smart_tests(self, package_path: str, test_scripts: List[str] = None) -> List[Dict[str, Any]]:
        """Run smart tests on the package"""
        executions = []
        
        # Use provided test scripts or generate smart ones
        scripts_to_run = test_scripts or self.generate_smart_test_scripts(package_path)
        
        for script in scripts_to_run:
            try:
                execution_result = self.execute_smart_test(script)
                if execution_result:
                    executions.append(execution_result)
            except Exception as e:
                print(f"Warning: Smart test execution failed for {script}: {e}")
                executions.append({
                    "script": script,
                    "status": "failed",
                    "error": str(e)
                })
        
        return executions
    
    def generate_smart_test_scripts(self, package_path: str) -> List[str]:
        """Generate smart test scripts for each module in the package"""
        test_scripts = []
        
        # Find all Python modules in the package
        python_modules = self.find_python_modules(package_path)
        
        # Limit the number of modules to prevent excessive processing
        max_modules = 10
        if len(python_modules) > max_modules:
            print(f"Found {len(python_modules)} modules, limiting to first {max_modules} for testing")
            python_modules = python_modules[:max_modules]
        
        for module_path in python_modules:
            try:
                test_script = self.create_smart_test_script(module_path)
                if test_script:
                    test_scripts.append(test_script)
            except Exception as e:
                print(f"Warning: Failed to create smart test for {module_path}: {e}")
        
        return test_scripts
    
    def find_python_modules(self, package_path: str) -> List[str]:
        """Find all Python modules in the package"""
        python_modules = []
        
        for root, dirs, files in os.walk(package_path):
            # Skip __pycache__ and other cache directories
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    python_modules.append(module_path)
        
        return python_modules
    
    def create_smart_test_script(self, module_path: str) -> Optional[str]:
        """Create a smart test script for a specific module"""
        try:
            # Analyze the module to extract callable items
            module_info = self.analyze_module(module_path)
            if not module_info:
                return None
            
            # Generate the test script content
            test_content = self.generate_test_script_content(module_info)
            
            # Save the test script
            module_name = module_info['module_name']
            test_script_path = os.path.join(self.temp_dir, f"smart_test_{module_name.replace('.', '_')}.py")
            
            with open(test_script_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            return test_script_path
            
        except Exception as e:
            print(f"Failed to create smart test script for {module_path}: {e}")
            return None
    
    def analyze_module(self, module_path: str) -> Optional[Dict[str, Any]]:
        """Analyze a module to extract functions and classes defined in it"""
        try:
            # Read and parse the module
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip very large files to prevent memory issues
            if len(content) > 1000000:  # 1MB limit
                print(f"Skipping large module {module_path} ({len(content)} bytes)")
                return None
            
            tree = ast.parse(content)
            
            # Extract module information
            pkg_root = self.package_path
            pkg_name = os.path.basename(pkg_root.rstrip(os.sep))
            
            # Calculate relative module path
            rel_path = os.path.relpath(module_path, pkg_root)
            module_rel = os.path.splitext(rel_path)[0].replace(os.sep, ".")
            full_module_name = f"{pkg_name}.{module_rel}"
            
            # Extract functions and classes defined in this module
            functions = self.extract_functions_from_ast(tree)
            classes = self.extract_classes_from_ast(tree)
            
            return {
                'module_path': module_path,
                'module_name': module_rel,
                'full_module_name': full_module_name,
                'package_name': pkg_name,
                'package_parent': os.path.dirname(pkg_root),
                'functions': functions,
                'classes': classes
            }
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Failed to parse module {module_path}: {e}")
            return None
        except Exception as e:
            print(f"Failed to analyze module {module_path}: {e}")
            return None
    
    def extract_functions_from_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions from AST"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions
                if not node.name.startswith('_'):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'defaults': len(node.args.defaults),
                        'has_varargs': node.args.vararg is not None,
                        'has_kwargs': node.args.kwarg is not None,
                        'required_args': len(node.args.args) - len(node.args.defaults)
                    }
                    functions.append(func_info)
        
        return functions
    
    def extract_classes_from_ast(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions from AST"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Skip private classes
                if not node.name.startswith('_'):
                    # Find __init__ method
                    init_info = None
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                            # Skip 'self' parameter
                            args = item.args.args[1:] if item.args.args else []
                            init_info = {
                                'args': [arg.arg for arg in args],
                                'defaults': len(item.args.defaults),
                                'has_varargs': item.args.vararg is not None,
                                'has_kwargs': item.args.kwarg is not None,
                                'required_args': len(args) - len(item.args.defaults)
                            }
                            break
                    
                    class_info = {
                        'name': node.name,
                        'init': init_info
                    }
                    classes.append(class_info)
        
        return classes
    
    def generate_test_script_content(self, module_info: Dict[str, Any]) -> str:
        """Generate the content of a smart test script"""
        lines = [
            "#!/usr/bin/env python3",
            "\"\"\"Smart auto-generated test script\"\"\"",
            "",
            "import sys",
            "import inspect",
            "import traceback",
            "",
            f"# Add package parent to Python path",
            f"sys.path.insert(0, {repr(module_info['package_parent'])})",
            "",
            "# Test results",
            "results = {",
            "    'module': " + repr(module_info['full_module_name']) + ",",
            "    'functions_tested': [],",
            "    'classes_tested': [],",
            "    'functions_skipped': [],",
            "    'classes_skipped': [],",
            "    'errors': []",
            "}",
            "",
            "try:",
            f"    import {module_info['full_module_name']} as target_module",
            f"    print(f'Successfully imported {module_info['full_module_name']}')",
            "",
            "    # Test functions",
            "    print('\\n=== Testing Functions ===')"
        ]
        
        # Add function tests
        for func in module_info['functions']:
            if func['required_args'] == 0:  # No required arguments
                lines.extend([
                    f"    # Test function: {func['name']}",
                    f"    if hasattr(target_module, '{func['name']}'):",
                    f"        func = getattr(target_module, '{func['name']}')",
                    f"        if inspect.isfunction(func) and func.__module__ == target_module.__name__:",
                    f"            try:",
                    f"                result = func()",
                    f"                print(f'✓ {func['name']}() -> {{type(result).__name__}}: {{repr(result)[:100]}}')",
                    f"                results['functions_tested'].append('{func['name']}')",
                    f"            except Exception as e:",
                    f"                print(f'✗ {func['name']}() failed: {{e}}')",
                    f"                results['errors'].append(f'{func['name']}: {{e}}')",
                    f"        else:",
                    f"            print(f'⚠ {func['name']} not defined in this module')",
                    f"    else:",
                    f"        print(f'⚠ {func['name']} not found in module')",
                    ""
                ])
            else:
                lines.extend([
                    f"    # Skipping function {func['name']} (requires {func['required_args']} arguments)",
                    f"    results['functions_skipped'].append('{func['name']}')",
                    f"    print(f'⏭ Skipping {func['name']}: requires {func['required_args']} arguments')",
                    ""
                ])
        
        # Add class tests
        lines.extend([
            "    # Test classes",
            "    print('\\n=== Testing Classes ===')"
        ])
        
        for cls in module_info['classes']:
            init_info = cls['init']
            if init_info is None or init_info['required_args'] == 0:  # No __init__ or no required args
                lines.extend([
                    f"    # Test class: {cls['name']}",
                    f"    if hasattr(target_module, '{cls['name']}'):",
                    f"        cls = getattr(target_module, '{cls['name']}')",
                    f"        if inspect.isclass(cls) and cls.__module__ == target_module.__name__:",
                    f"            try:",
                    f"                instance = cls()",
                    f"                print(f'✓ Created {cls['name']} instance: {{type(instance).__name__}}')",
                    f"                results['classes_tested'].append('{cls['name']}')",
                    f"                ",
                    f"                # Try to call some methods if they exist",
                    f"                for method_name in dir(instance):",
                    f"                    if not method_name.startswith('_') and callable(getattr(instance, method_name)):",
                    f"                        try:",
                    f"                            method = getattr(instance, method_name)",
                    f"                            sig = inspect.signature(method)",
                    f"                            # Only call methods with no required parameters",
                    f"                            required_params = sum(1 for p in sig.parameters.values() if p.default is inspect.Parameter.empty)",
                    f"                            if required_params == 0:",
                    f"                                result = method()",
                    f"                                print(f'  ✓ {{method_name}}() -> {{type(result).__name__}}: {{repr(result)[:50]}}')",
                    f"                        except Exception as e:",
                    f"                            print(f'  ✗ {{method_name}}() failed: {{e}}')",
                    f"            except Exception as e:",
                    f"                print(f'✗ Failed to create {cls['name']}: {{e}}')",
                    f"                results['errors'].append(f'{cls['name']}: {{e}}')",
                    f"        else:",
                    f"            print(f'⚠ {cls['name']} not defined in this module')",
                    f"    else:",
                    f"        print(f'⚠ {cls['name']} not found in module')",
                    ""
                ])
            else:
                required_args = init_info['required_args']
                lines.extend([
                    f"    # Skipping class {cls['name']} (requires {required_args} constructor arguments)",
                    f"    results['classes_skipped'].append('{cls['name']}')",
                    f"    print(f'⏭ Skipping {cls['name']}: requires {required_args} constructor arguments')",
                    ""
                ])
        
        # Add summary and error handling
        lines.extend([
            "",
            "except ImportError as e:",
            f"    print(f'Failed to import {module_info['full_module_name']}: {{e}}')",
            "    results['errors'].append(f'Import error: {e}')",
            "except Exception as e:",
            "    print(f'Unexpected error: {e}')",
            "    results['errors'].append(f'Unexpected error: {e}')",
            "    traceback.print_exc()",
            "",
            "# Print summary",
            "print('\\n=== Test Summary ===')",
            "print(f'Functions tested: {len(results[\"functions_tested\"])}')",
            "print(f'Classes tested: {len(results[\"classes_tested\"])}')",
            "print(f'Functions skipped: {len(results[\"functions_skipped\"])}')",
            "print(f'Classes skipped: {len(results[\"classes_skipped\"])}')",
            "print(f'Errors: {len(results[\"errors\"])}')",
            "",
            "if results['errors']:",
            "    print('\\nErrors encountered:')",
            "    for error in results['errors']:",
            "        print(f'  - {error}')",
            "",
            "# Output results as JSON for programmatic access",
            "import json",
            "print('\\n=== JSON Results ===')",
            "print(json.dumps(results, indent=2))"
        ])
        
        return '\n'.join(lines)
    
    def execute_smart_test(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Execute a smart test script and capture results"""
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.temp_dir
            )
            
            # Parse the output to extract JSON results
            stdout_lines = result.stdout.split('\n')
            json_results = None
            
            # Look for JSON results section
            in_json_section = False
            json_lines = []
            
            for line in stdout_lines:
                if line.strip() == '=== JSON Results ===':
                    in_json_section = True
                    continue
                elif in_json_section:
                    json_lines.append(line)
            
            if json_lines:
                try:
                    json_text = '\n'.join(json_lines).strip()
                    json_results = json.loads(json_text)
                except json.JSONDecodeError:
                    json_results = None
            
            return {
                "@type": "SmartTestExecution",
                "script": script_path,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "results": json_results,
                "success": result.returncode == 0,
                "execution_summary": self.extract_execution_summary_from_output(result.stdout)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "@type": "SmartTestExecution",
                "script": script_path,
                "exit_code": -1,
                "error": "Test execution timed out",
                "success": False
            }
        except Exception as e:
            return {
                "@type": "SmartTestExecution",
                "script": script_path,
                "error": str(e),
                "success": False
            }
    
    def extract_execution_summary_from_output(self, output: str) -> Dict[str, Any]:
        """Extract execution summary from test output"""
        summary = {
            "functions_called": [],
            "classes_instantiated": [],
            "methods_called": [],
            "errors": []
        }
        
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('✓') and '() ->' in line:
                # Function call
                func_name = line.split('✓')[1].split('()')[0].strip()
                summary["functions_called"].append(func_name)
            elif line.startswith('✓ Created') and 'instance:' in line:
                # Class instantiation
                class_name = line.split('Created')[1].split('instance:')[0].strip()
                summary["classes_instantiated"].append(class_name)
            elif line.startswith('  ✓') and '() ->' in line:
                # Method call
                method_name = line.split('✓')[1].split('()')[0].strip()
                summary["methods_called"].append(method_name)
            elif line.startswith('✗'):
                # Error
                error_desc = line.split('✗')[1].strip()
                summary["errors"].append(error_desc)
        
        return summary
    
    def generate_execution_summary(self) -> Dict[str, Any]:
        """Generate overall execution summary"""
        # This would be populated after running all tests
        return {
            "@type": "ExecutionSummary",
            "total_modules_tested": 0,
            "total_functions_tested": 0,
            "total_classes_tested": 0,
            "total_errors": 0,
            "test_coverage": "smart_introspection"
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Cleanup failed: {e}")


def extract_smart_runtime_behavior(package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
    """Main function to extract runtime behavior using smart test generation"""
    extractor = SmartRuntimeBehaviorExtractor()
    try:
        return extractor.extract_runtime_behavior(package_path, test_scripts)
    finally:
        extractor.cleanup()