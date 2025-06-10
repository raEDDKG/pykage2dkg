# extractor/type_analyzer.py
import subprocess
import json
import tempfile
import os
from typing import Dict, List, Any, Optional

class TypeAnalyzer:
    def __init__(self):
        self.pyright_available = self._check_pyright()
        self.mypy_available = self._check_mypy()
    
    def _check_pyright(self) -> bool:
        try:
            subprocess.run(['pyright', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_mypy(self) -> bool:
        try:
            subprocess.run(['mypy', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def analyze_types(self, project_path: str) -> Dict[str, Any]:
        """Run type analysis using available tools"""
        results = {
            "@type": "TypeAnalysis",
            "pyright": self._run_pyright(project_path) if self.pyright_available else None,
            "mypy": self._run_mypy(project_path) if self.mypy_available else None,
            "summary": {}
        }
        
        # Combine results
        results["summary"] = self._combine_type_results(results)
        return results
    
    def _run_pyright(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Run Pyright type checker"""
        try:
            cmd = ['pyright', '--outputjson', project_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.stdout:
                pyright_data = json.loads(result.stdout)
                return {
                    "tool": "pyright",
                    "diagnostics": self._transform_pyright_diagnostics(pyright_data.get('generalDiagnostics', [])),
                    "summary": pyright_data.get('summary', {}),
                    "typeCompleteness": pyright_data.get('typeCompleteness', {})
                }
        except Exception as e:
            print(f"Pyright analysis failed: {e}")
        return None
    
    def _run_mypy(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Run MyPy type checker"""
        try:
            cmd = ['mypy', '--show-error-codes', '--json-report', '/tmp/mypy-report', project_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse mypy output
            diagnostics = []
            for line in result.stdout.split('\n'):
                if line.strip() and ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        diagnostics.append({
                            "file": parts[0],
                            "line": int(parts[1]) if parts[1].isdigit() else 0,
                            "column": int(parts[2]) if parts[2].isdigit() else 0,
                            "message": parts[3].strip(),
                            "severity": "error" if "error:" in line else "warning"
                        })
            
            return {
                "tool": "mypy",
                "diagnostics": diagnostics,
                "returnCode": result.returncode
            }
        except Exception as e:
            print(f"MyPy analysis failed: {e}")
        return None
    
    def _transform_pyright_diagnostics(self, diagnostics: List[Dict]) -> List[Dict[str, Any]]:
        """Transform Pyright diagnostics to our schema"""
        return [{
            "@type": "TypeDiagnostic",
            "file": diag.get('file', ''),
            "line": diag.get('range', {}).get('start', {}).get('line', 0) + 1,
            "column": diag.get('range', {}).get('start', {}).get('character', 0) + 1,
            "message": diag.get('message', ''),
            "severity": diag.get('severity', 'error'),
            "rule": diag.get('rule', ''),
            "category": "type-checking"
        } for diag in diagnostics]
    
    def _combine_type_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine type analysis results into summary"""
        total_errors = 0
        total_warnings = 0
        files_analyzed = set()
        
        for tool_name in ['pyright', 'mypy']:
            tool_result = results.get(tool_name)
            if tool_result and 'diagnostics' in tool_result:
                for diag in tool_result['diagnostics']:
                    files_analyzed.add(diag.get('file', ''))
                    if diag.get('severity') == 'error':
                        total_errors += 1
                    else:
                        total_warnings += 1
        
        return {
            "totalErrors": total_errors,
            "totalWarnings": total_warnings,
            "filesAnalyzed": len(files_analyzed),
            "toolsUsed": [tool for tool in ['pyright', 'mypy'] if results.get(tool) is not None]
        }