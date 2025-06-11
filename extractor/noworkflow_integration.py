#!/usr/bin/env python3

"""
Practical noWorkflow integration that works with real packages.
Converts noWorkflow's Prolog output to JSON-LD format.
"""

import os
import re
import json
import subprocess
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from .runtime_extractor import extract_runtime_behavior

class NoWorkflowIntegrator:
    """Integrates noWorkflow runtime analysis into the JSON-LD pipeline"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='noworkflow_')
    
    def analyze_package_runtime(self, package_path: str) -> Dict[str, Any]:
        """
        Analyze a Python package using noWorkflow and return JSON-LD formatted results
        """
        
        print(f"🔄 Analyzing runtime behavior for: {package_path}")
        
         # first try our new, inspect-based harness (which still uses noWorkflow for provenance)
        try:
            return extract_runtime_behavior(package_path)
        except ImportError:
             # fallback to the legacy noWorkflow-only logic
            print("⚠️ runtime_extractor not found, falling back to built-in noWorkflow harness")
            test_scripts = self.find_executable_scripts(package_path)
            if not test_scripts:
                print("⚠️ No executable scripts found, creating simple test script")
                test_scripts = [self.create_simple_test_script(package_path)]
        
        runtime_data = {
            "@type": "RuntimeBehavior",
            "@context": {
                "prov": "http://www.w3.org/ns/prov#",
                "now": "https://github.com/gems-uff/noworkflow#"
            },
            "tool": "noWorkflow",
            "version": self.get_noworkflow_version(),
            "executions": []
        }
        
        # Run each test script with noWorkflow
        for script in test_scripts:
            try:
                execution_data = self.run_script_with_noworkflow(script)
                if execution_data:
                    runtime_data["executions"].append(execution_data)
            except Exception as e:
                print(f"⚠️ Failed to analyze {script}: {e}")
                runtime_data["executions"].append({
                    "script": script,
                    "error": str(e),
                    "status": "failed"
                })
        
        return runtime_data
    
    def find_executable_scripts(self, package_path: str) -> List[str]:
        """Find scripts that can be executed with noWorkflow"""
        
        executable_scripts = []
        
        # Look for common test/demo files
        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    
                    # Check if it's likely executable
                    if any(pattern in file.lower() for pattern in [
                        'test_', 'demo', 'example', 'main', 'run', 'cli'
                    ]):
                        if self.is_script_executable(full_path):
                            executable_scripts.append(full_path)
        
        return executable_scripts[:3]  # Limit to 3 scripts for safety
    
    def is_script_executable(self, script_path: str) -> bool:
        """Check if a script is likely executable (has main block or simple structure)"""
        
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for main block
            if 'if __name__ == "__main__"' in content:
                return True
            
            # Check for simple function calls at module level
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('import') and not line.startswith('from'):
                    if '(' in line and ')' in line and not line.startswith('def ') and not line.startswith('class '):
                        return True
            
            return False
            
        except Exception:
            return False
    
    def create_simple_test_script(self, package_path: str) -> str:
        """Create a simple test script for the package"""
        
        # Find Python files to import
        python_files = []
        for root, dirs, files in os.walk(package_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    rel_path = os.path.relpath(os.path.join(root, file), package_path)
                    module_name = rel_path.replace('/', '.').replace('\\', '.')[:-3]
                    python_files.append((module_name, os.path.join(root, file)))
        
        # Create test script
        test_script_content = f'''#!/usr/bin/env python3
"""Auto-generated test script for noWorkflow analysis"""

import sys
import os
sys.path.insert(0, r"{package_path}")

print("=== noWorkflow Runtime Analysis ===")

# Test imports and basic functionality
'''
        
        for module_name, file_path in python_files[:3]:  # Limit to 3 modules
            test_script_content += f'''
try:
    print(f"Testing module: {module_name}")
    import {module_name}
    
    # Try to find and call simple functions
    for attr_name in dir({module_name}):
        if not attr_name.startswith('_'):
            attr = getattr({module_name}, attr_name)
            if callable(attr):
                try:
                    print(f"  Found function: {{attr_name}}")
                    # Try calling with no arguments
                    result = attr()
                    print(f"  {{attr_name}}() -> {{result}}")
                except Exception as e:
                    print(f"  {{attr_name}}() failed: {{e}}")
                    
except Exception as e:
    print(f"Failed to test {module_name}: {{e}}")
'''
        
        test_script_content += '''
print("=== Analysis Complete ===")
'''
        
        # Save test script
        test_script_path = os.path.join(self.temp_dir, 'auto_test.py')
        with open(test_script_path, 'w') as f:
            f.write(test_script_content)
        
        return test_script_path
    
    def run_script_with_noworkflow(self, script_path: str) -> Optional[Dict[str, Any]]:
        """Run a script with noWorkflow and extract the results"""
        
        print(f"  🔄 Running {os.path.basename(script_path)} with noWorkflow...")
        
        try:
            # Change to the script's directory
            script_dir = os.path.dirname(script_path)
            script_name = os.path.basename(script_path)
            
            # Run with noWorkflow
            result = subprocess.run(
                ['now', 'run', script_name],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"    ⚠️ Script execution failed: {result.stderr}")
                return None
            
            print(f"    ✅ Script executed successfully")
            
            # Export the provenance data
            export_result = subprocess.run(
                ['now', 'export', '1'],  # Export latest trial
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if export_result.returncode != 0:
                print(f"    ⚠️ Export failed: {export_result.stderr}")
                return None
            
            # Parse the Prolog output and convert to JSON-LD
            provenance_data = self.parse_prolog_to_jsonld(export_result.stdout)
            
            return {
                "@type": "ScriptExecution",
                "script": script_path,
                "stdout": result.stdout,
                "executionTime": self.extract_execution_time(export_result.stdout),
                "provenance": provenance_data,
                "status": "success"
            }
            
        except subprocess.TimeoutExpired:
            print(f"    ⚠️ Script execution timed out")
            return None
        except Exception as e:
            print(f"    ⚠️ Error running script: {e}")
            return None
    
    def parse_prolog_to_jsonld(self, prolog_output: str) -> Dict[str, Any]:
        """Convert noWorkflow's Prolog output to JSON-LD format"""
        
        # Extract key information from Prolog facts
        trial_info = self.extract_trial_info(prolog_output)
        function_calls = self.extract_function_calls(prolog_output)
        variable_accesses = self.extract_variable_accesses(prolog_output)
        
        return {
            "@type": "ProvenanceData",
            "@context": {"prov": "http://www.w3.org/ns/prov#"},
            "trial": trial_info,
            "activities": function_calls,
            "entities": variable_accesses,
            "format": "PROV-inspired-JSON-LD"
        }
    
    def extract_trial_info(self, prolog_output: str) -> Dict[str, Any]:
        """Extract trial information from Prolog output"""
        
        # Look for trial fact: trial(Id, Script, Start, Finish, Command, Status, ...)
        trial_match = re.search(r"trial\('([^']+)', '([^']+)', ([^,]+), ([^,]+), '([^']+)', '([^']+)'", prolog_output)
        
        if trial_match:
            trial_id, script, start_time, finish_time, command, status = trial_match.groups()
            
            return {
                "@type": "prov:Activity",
                "@id": f"trial:{trial_id}",
                "script": script,
                "startTime": float(start_time),
                "endTime": float(finish_time),
                "duration": float(finish_time) - float(start_time),
                "command": command,
                "status": status
            }
        
        return {"@type": "prov:Activity", "error": "Could not parse trial info"}
    
    def extract_function_calls(self, prolog_output: str) -> List[Dict[str, Any]]:
        """Extract function call information from Prolog output"""
        
        function_calls = []
        
        # Look for function_activation facts
        activation_pattern = r"function_activation\('([^']+)', (\d+), '([^']+)', (\d+), ([^,]+), ([^,]+)"
        
        for match in re.finditer(activation_pattern, prolog_output):
            trial_id, activation_id, function_name, line, start_time, end_time = match.groups()
            
            function_calls.append({
                "@type": "prov:Activity",
                "@id": f"activation:{activation_id}",
                "name": function_name,
                "line": int(line),
                "startTime": float(start_time),
                "endTime": float(end_time),
                "duration": float(end_time) - float(start_time),
                "trial": trial_id
            })
        
        return function_calls
    
    def extract_variable_accesses(self, prolog_output: str) -> List[Dict[str, Any]]:
        """Extract variable access information from Prolog output"""
        
        variables = []
        
        # Look for variable facts
        variable_pattern = r"variable\('([^']+)', (\d+), '([^']+)', '([^']+)', ([^,]+), '([^']+)'"
        
        for match in re.finditer(variable_pattern, prolog_output):
            trial_id, var_id, name, value, timestamp, context = match.groups()
            
            variables.append({
                "@type": "prov:Entity",
                "@id": f"variable:{var_id}",
                "name": name,
                "value": value,
                "timestamp": float(timestamp),
                "context": context,
                "trial": trial_id
            })
        
        return variables
    
    def extract_execution_time(self, prolog_output: str) -> Optional[float]:
        """Extract execution time from trial info"""
        
        trial_match = re.search(r"trial\('[^']+', '[^']+', ([^,]+), ([^,]+),", prolog_output)
        if trial_match:
            start_time, end_time = trial_match.groups()
            return float(end_time) - float(start_time)
        
        return None
    
    def get_noworkflow_version(self) -> str:
        """Get noWorkflow version"""
        try:
            result = subprocess.run(['now', '--version'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Cleanup failed: {e}")

def integrate_noworkflow_runtime(package_path: str) -> Dict[str, Any]:
    """Main function to integrate noWorkflow runtime analysis"""
    
    integrator = NoWorkflowIntegrator()
    try:
        return integrator.analyze_package_runtime(package_path)
    finally:
        integrator.cleanup()

def main():
    """Demo the noWorkflow integration"""
    
    print("🚀 noWorkflow Integration Demo")
    print("=" * 50)
    
    # Test with current package
    package_path = "extractor"
    
    if os.path.exists(package_path):
        runtime_data = integrate_noworkflow_runtime(package_path)
        
        # Save results
        output_file = "output_jsonld/noworkflow_runtime_analysis.jsonld"
        os.makedirs("output_jsonld", exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(runtime_data, f, indent=2)
        
        print(f"\n✅ Runtime analysis saved to: {output_file}")
        
        # Show summary
        print(f"\n📊 Analysis Summary:")
        print(f"   Tool: {runtime_data.get('tool')}")
        print(f"   Version: {runtime_data.get('version')}")
        print(f"   Executions: {len(runtime_data.get('executions', []))}")
        
        for i, execution in enumerate(runtime_data.get('executions', [])):
            print(f"   Execution {i+1}: {execution.get('status', 'unknown')}")
            if 'provenance' in execution:
                prov = execution['provenance']
                print(f"     Activities: {len(prov.get('activities', []))}")
                print(f"     Entities: {len(prov.get('entities', []))}")
    
    else:
        print(f"❌ Package path not found: {package_path}")

if __name__ == "__main__":
    main()