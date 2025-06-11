#!/usr/bin/env python3

"""
Runtime behavior extractor that integrates provenance and execution tracing
into the JSON-LD pipeline using noWorkflow, OpenTelemetry, and PROV-JSONLD.
"""

import os
import sys
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from opentelemetry import trace
    #from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

try:
    import prov.model as prov
    PROV_AVAILABLE = True
except ImportError:
    PROV_AVAILABLE = False

class RuntimeBehaviorExtractor:
    """Extract runtime behavior and provenance information"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='runtime_analysis_')
        self.setup_tracing()
    
    def setup_tracing(self):
        """Setup OpenTelemetry tracing if available"""
        if OPENTELEMETRY_AVAILABLE:
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = None
    
    def extract_runtime_behavior(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """
        Extract runtime behavior using multiple approaches:
        1. noWorkflow for automatic provenance
        2. OpenTelemetry for tracing
        3. Custom execution analysis
        """
        
        runtime_data = {
            "@type": "RuntimeBehavior",
            "provenance": self.extract_provenance_with_noworkflow(package_path, test_scripts),
            "traces": self.extract_opentelemetry_traces(package_path, test_scripts),
            "executions": self.extract_execution_patterns(package_path, test_scripts),
            "dataFlow": self.extract_runtime_data_flow(package_path, test_scripts)
        }
        
        return runtime_data
    
    def extract_provenance_with_noworkflow(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """Use noWorkflow to capture execution provenance"""
        
        if not self.check_noworkflow_available():
            return {"error": "noWorkflow not available", "data": []}
        
        provenance_data = []
        
        # Find test scripts or create simple execution scripts
        scripts_to_run = test_scripts or self.find_or_create_test_scripts(package_path)
        
        for script in scripts_to_run:
            try:
                # Run with noWorkflow
                result = self.run_with_noworkflow(script)
                if result:
                    provenance_data.append(result)
            except Exception as e:
                print(f"Warning: noWorkflow execution failed for {script}: {e}")
        
        return {
            "@type": "ProvenanceData",
            "tool": "noWorkflow",
            "format": "PROV-JSONLD",
            "executions": provenance_data
        }
    
    def run_with_noworkflow(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Run a script with noWorkflow and extract PROV data"""
        
        try:
            # Run noWorkflow
            cmd = ["now", "run", script_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return None
            
            # Export provenance as PROV-JSONLD
            export_cmd = ["now", "export", "--format", "prov-json"]
            export_result = subprocess.run(export_cmd, capture_output=True, text=True)
            
            if export_result.returncode == 0:
                prov_data = json.loads(export_result.stdout)
                return self.convert_prov_to_jsonld(prov_data)
            
        except Exception as e:
            print(f"noWorkflow execution error: {e}")
        
        return None
    
    def convert_prov_to_jsonld(self, prov_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert PROV data to JSON-LD format"""
        
        return {
            "@context": {
                "prov": "http://www.w3.org/ns/prov#",
                "activity": "prov:Activity",
                "entity": "prov:Entity", 
                "agent": "prov:Agent",
                "used": "prov:used",
                "generated": "prov:wasGeneratedBy"
            },
            "@type": "prov:Bundle",
            "activities": self.extract_activities(prov_data),
            "entities": self.extract_entities(prov_data),
            "relationships": self.extract_relationships(prov_data)
        }
    
    def extract_opentelemetry_traces(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """Extract OpenTelemetry traces from instrumented code"""
        
        if not OPENTELEMETRY_AVAILABLE:
            return {"error": "OpenTelemetry not available", "traces": []}
        
        traces = []
        
        # Auto-instrument the package
        instrumented_scripts = self.create_instrumented_scripts(package_path, test_scripts)
        
        for script in instrumented_scripts:
            try:
                trace_data = self.run_with_opentelemetry(script)
                if trace_data:
                    traces.append(trace_data)
            except Exception as e:
                print(f"Warning: OpenTelemetry tracing failed for {script}: {e}")
        
        return {
            "@type": "TracingData",
            "tool": "OpenTelemetry",
            "format": "OTLP-JSON-LD",
            "traces": traces
        }
    
    def create_instrumented_scripts(self, package_path: str, test_scripts: List[str] = None) -> List[str]:
        """Create auto-instrumented versions of scripts"""
        
        instrumented_scripts = []
        scripts_to_instrument = test_scripts or self.find_or_create_test_scripts(package_path)
        
        for script in scripts_to_instrument:
            instrumented_path = self.add_opentelemetry_instrumentation(script)
            if instrumented_path:
                instrumented_scripts.append(instrumented_path)
        
        return instrumented_scripts
    
    def add_opentelemetry_instrumentation(self, script_path: str) -> Optional[str]:
        """Add OpenTelemetry instrumentation to a script"""
        
        try:
            with open(script_path, 'r') as f:
                original_code = f.read()
            
            # Add instrumentation wrapper
            instrumented_code = f'''
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.instrumentation.auto_instrumentation import sitecustomize

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Auto-instrument
sitecustomize.instrument()

# Original code with tracing
with tracer.start_as_current_span("script_execution"):
{self.indent_code(original_code, "    ")}
'''
            
            # Save instrumented version
            instrumented_path = os.path.join(self.temp_dir, f"instrumented_{os.path.basename(script_path)}")
            with open(instrumented_path, 'w') as f:
                f.write(instrumented_code)
            
            return instrumented_path
            
        except Exception as e:
            print(f"Instrumentation failed for {script_path}: {e}")
            return None
    
    def extract_execution_patterns(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """Extract execution patterns through custom analysis"""
        
        patterns = {
            "@type": "ExecutionPatterns",
            "functionCalls": [],
            "dataTransformations": [],
            "controlFlowPaths": [],
            "performanceMetrics": []
        }
        
        scripts_to_analyze = test_scripts or self.find_or_create_test_scripts(package_path)
        
        for script in scripts_to_analyze:
            try:
                execution_data = self.analyze_script_execution(script)
                if execution_data:
                    patterns["functionCalls"].extend(execution_data.get("functionCalls", []))
                    patterns["dataTransformations"].extend(execution_data.get("dataTransformations", []))
                    patterns["controlFlowPaths"].extend(execution_data.get("controlFlowPaths", []))
                    patterns["performanceMetrics"].extend(execution_data.get("performanceMetrics", []))
            except Exception as e:
                print(f"Warning: Execution analysis failed for {script}: {e}")
        
        return patterns
    
    def find_or_create_test_scripts(self, package_path: str) -> List[str]:
        """Find existing test scripts or create simple ones"""
        
        test_scripts = []
        
        # Look for existing test files
        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_scripts.append(os.path.join(root, file))
                elif file in ['example.py', 'demo.py', 'main.py']:
                    test_scripts.append(os.path.join(root, file))
        
        # If no tests found, create simple execution scripts
        if not test_scripts:
            test_scripts = self.create_simple_test_scripts(package_path)
        
        return test_scripts
    
    def create_simple_test_scripts(self, package_path: str) -> List[str]:
        """Create simple test scripts that exercise the package"""
        
        test_scripts = []
        
        # Find Python files to analyze
        python_files = []
        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(os.path.join(root, file))
        
        # Create test scripts for each module
        for py_file in python_files[:3]:  # Limit to first 3 files
            test_script = self.create_test_script_for_module(py_file)
            if test_script:
                test_scripts.append(test_script)
        
        return test_scripts
    
    def create_test_script_for_module(self, module_path: str) -> Optional[str]:
        """Create a simple test script for a module"""
        
        try:
            # Analyze the module to find classes and functions
            with open(module_path, 'r') as f:
                content = f.read()
            
            # Simple extraction of class and function names
            import ast
            tree = ast.parse(content)
            
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    functions.append(node.name)
            
            # Create test script
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            test_content = f'''
#!/usr/bin/env python3
"""Auto-generated test script for {module_name}"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from {module_name} import *
    
    print(f"Testing module: {module_name}")
    
    # Test classes
'''
            
            for class_name in classes:
                test_content += f'''
    try:
        print(f"Testing class: {class_name}")
        obj = {class_name}()
        print(f"Created {class_name} instance")
    except Exception as e:
        print(f"Failed to test {class_name}: {{e}}")
'''
            
            for func_name in functions:
                test_content += f'''
    try:
        print(f"Testing function: {func_name}")
        # Try calling with no args first
        result = {func_name}()
        print(f"{func_name}() returned: {{result}}")
    except Exception as e:
        print(f"Failed to test {func_name}: {{e}}")
'''
            
            test_content += '''
except Exception as e:
    print(f"Failed to import module: {e}")
'''
            
            # Save test script
            test_script_path = os.path.join(self.temp_dir, f"test_{module_name}.py")
            with open(test_script_path, 'w') as f:
                f.write(test_content)
            
            return test_script_path
            
        except Exception as e:
            print(f"Failed to create test script for {module_path}: {e}")
            return None
    
    def check_noworkflow_available(self) -> bool:
        """Check if noWorkflow is available"""
        try:
            result = subprocess.run(["now", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def indent_code(self, code: str, indent: str) -> str:
        """Indent code block"""
        return '\n'.join(indent + line for line in code.split('\n'))
    
    def extract_activities(self, prov_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract activities from PROV data"""
        activities = []
        
        for key, value in prov_data.get('activity', {}).items():
            activities.append({
                "@type": "prov:Activity",
                "@id": key,
                "label": value.get('prov:label', [{}])[0].get('$', key),
                "startTime": value.get('prov:startTime', [{}])[0].get('$'),
                "endTime": value.get('prov:endTime', [{}])[0].get('$')
            })
        
        return activities
    
    def extract_entities(self, prov_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entities from PROV data"""
        entities = []
        
        for key, value in prov_data.get('entity', {}).items():
            entities.append({
                "@type": "prov:Entity", 
                "@id": key,
                "label": value.get('prov:label', [{}])[0].get('$', key),
                "value": value.get('prov:value', [{}])[0].get('$')
            })
        
        return entities
    
    def extract_relationships(self, prov_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships from PROV data"""
        relationships = []
        
        # Extract usage relationships
        for key, value in prov_data.get('used', {}).items():
            relationships.append({
                "@type": "prov:Usage",
                "@id": key,
                "activity": value.get('prov:activity'),
                "entity": value.get('prov:entity')
            })
        
        # Extract generation relationships
        for key, value in prov_data.get('wasGeneratedBy', {}).items():
            relationships.append({
                "@type": "prov:Generation",
                "@id": key,
                "entity": value.get('prov:entity'),
                "activity": value.get('prov:activity')
            })
        
        return relationships
    
    def analyze_script_execution(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Analyze script execution patterns"""
        
        try:
            # Run script and capture output
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=10)
            
            return {
                "script": script_path,
                "exitCode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "functionCalls": self.extract_function_calls_from_output(result.stdout),
                "dataTransformations": [],
                "controlFlowPaths": [],
                "performanceMetrics": []
            }
            
        except Exception as e:
            print(f"Script execution analysis failed: {e}")
            return None
    
    def extract_function_calls_from_output(self, output: str) -> List[Dict[str, Any]]:
        """Extract function call information from script output"""
        
        function_calls = []
        
        for line in output.split('\n'):
            if 'Testing function:' in line:
                func_name = line.split('Testing function:')[1].strip()
                function_calls.append({
                    "@type": "FunctionCall",
                    "name": func_name,
                    "timestamp": "runtime",
                    "success": True
                })
            elif 'Failed to test' in line and 'function' in line:
                func_name = line.split('Failed to test')[1].split(':')[0].strip()
                function_calls.append({
                    "@type": "FunctionCall", 
                    "name": func_name,
                    "timestamp": "runtime",
                    "success": False,
                    "error": line.split(':')[-1].strip()
                })
        
        return function_calls
    
    def run_with_opentelemetry(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Run script with OpenTelemetry and capture traces"""
        
        try:
            # Run instrumented script
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=30)
            
            # For now, return basic trace info
            # In a full implementation, you'd capture actual OTLP traces
            return {
                "@type": "TraceData",
                "script": script_path,
                "spans": [
                    {
                        "@type": "Span",
                        "name": "script_execution",
                        "startTime": "runtime",
                        "endTime": "runtime",
                        "attributes": {
                            "script.path": script_path,
                            "script.exit_code": result.returncode
                        }
                    }
                ]
            }
            
        except Exception as e:
            print(f"OpenTelemetry tracing failed: {e}")
            return None
    
    def extract_runtime_data_flow(self, package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
        """Extract runtime data flow patterns"""
        
        return {
            "@type": "RuntimeDataFlow",
            "inputSources": [],
            "outputDestinations": [],
            "transformationChains": [],
            "dataTypes": []
        }
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Cleanup failed: {e}")

def extract_runtime_behavior(package_path: str, test_scripts: List[str] = None) -> Dict[str, Any]:
    """Main function to extract runtime behavior using noWorkflow"""
    
    try:
        # Try to use noWorkflow integration
        from .noworkflow_integration import integrate_noworkflow_runtime
        return integrate_noworkflow_runtime(package_path)
    except ImportError:
        # Fallback to basic extraction
        extractor = RuntimeBehaviorExtractor()
        try:
            return extractor.extract_runtime_behavior(package_path, test_scripts)
        finally:
            extractor.cleanup()
    except Exception as e:
        # If noWorkflow fails, return basic structure with error
        return {
            "@type": "RuntimeBehavior",
            "tool": "noWorkflow",
            "error": f"noWorkflow analysis failed: {str(e)}",
            "fallback": "basic_analysis",
            "executions": []
        }