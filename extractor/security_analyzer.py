# extractor/security_analyzer.py
import subprocess
import json
import tempfile
import os
from typing import Dict, List, Any, Optional

class SecurityAnalyzer:
    def __init__(self):
        self.bandit_available = self._check_bandit()
        self.codeql_available = self._check_codeql()
    
    def _check_bandit(self) -> bool:
        try:
            subprocess.run(['bandit', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _check_codeql(self) -> bool:
        try:
            subprocess.run(['codeql', 'version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def analyze_security(self, project_path: str) -> Dict[str, Any]:
        """Run security analysis using available tools"""
        results = {
            "@type": "SecurityAnalysis",
            "bandit": self._run_bandit(project_path) if self.bandit_available else None,
            "codeql": self._run_codeql(project_path) if self.codeql_available else None,
            "summary": {}
        }
        
        results["summary"] = self._combine_security_results(results)
        return results
    
    def _run_bandit(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Run Bandit security scanner"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            cmd = ['bandit', '-r', project_path, '-f', 'json', '-o', tmp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if os.path.exists(tmp_path):
                with open(tmp_path, 'r') as f:
                    bandit_data = json.load(f)
                
                return {
                    "tool": "bandit",
                    "vulnerabilities": self._transform_bandit_results(bandit_data.get('results', [])),
                    "metrics": bandit_data.get('metrics', {}),
                    "skippedTests": bandit_data.get('skipped', [])
                }
        except Exception as e:
            print(f"Bandit analysis failed: {e}")
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        return None
    
    def _run_codeql(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Run CodeQL analysis"""
        try:
            # Create CodeQL database
            db_path = tempfile.mkdtemp(prefix='codeql-db-')
            
            # Create database
            create_cmd = ['codeql', 'database', 'create', db_path, '--language=python', f'--source-root={project_path}']
            create_result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=300)
            
            if create_result.returncode != 0:
                return {"error": f"CodeQL database creation failed: {create_result.stderr}"}
            
            # Run analysis
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as tmp_file:
                sarif_path = tmp_file.name
            
            analyze_cmd = [
                'codeql', 'database', 'analyze', db_path,
                '--format=sarif-latest',
                f'--output={sarif_path}',
                'python-security-and-quality'
            ]
            analyze_result = subprocess.run(analyze_cmd, capture_output=True, text=True, timeout=300)
            
            if analyze_result.returncode == 0 and os.path.exists(sarif_path):
                with open(sarif_path, 'r') as f:
                    sarif_data = json.load(f)
                
                return {
                    "tool": "codeql",
                    "vulnerabilities": self._transform_codeql_results(sarif_data),
                    "format": "sarif"
                }
            else:
                return {"error": f"CodeQL analysis failed: {analyze_result.stderr}"}
                
        except Exception as e:
            print(f"CodeQL analysis failed: {e}")
            return {"error": str(e)}
        finally:
            # Cleanup
            if 'db_path' in locals():
                subprocess.run(['rm', '-rf', db_path], capture_output=True)
            if 'sarif_path' in locals() and os.path.exists(sarif_path):
                os.unlink(sarif_path)
        return None
    
    def _transform_bandit_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Transform Bandit results to our schema"""
        return [{
            "@type": "SecurityVulnerability",
            "tool": "bandit",
            "testId": result.get('test_id', ''),
            "testName": result.get('test_name', ''),
            "severity": result.get('issue_severity', 'UNKNOWN'),
            "confidence": result.get('issue_confidence', 'UNKNOWN'),
            "file": result.get('filename', ''),
            "line": result.get('line_number', 0),
            "code": result.get('code', ''),
            "message": result.get('issue_text', ''),
            "cwe": result.get('issue_cwe', {}).get('id') if result.get('issue_cwe') else None,
            "moreInfo": result.get('more_info', '')
        } for result in results]
    
    def _transform_codeql_results(self, sarif_data: Dict) -> List[Dict[str, Any]]:
        """Transform CodeQL SARIF results to our schema"""
        vulnerabilities = []
        
        for run in sarif_data.get('runs', []):
            for result in run.get('results', []):
                rule_id = result.get('ruleId', '')
                message = result.get('message', {}).get('text', '')
                
                for location in result.get('locations', []):
                    physical_location = location.get('physicalLocation', {})
                    artifact_location = physical_location.get('artifactLocation', {})
                    region = physical_location.get('region', {})
                    
                    vuln = {
                        "@type": "SecurityVulnerability",
                        "tool": "codeql",
                        "ruleId": rule_id,
                        "message": message,
                        "file": artifact_location.get('uri', ''),
                        "line": region.get('startLine', 0),
                        "column": region.get('startColumn', 0),
                        "severity": result.get('level', 'note'),
                        "snippet": region.get('snippet', {}).get('text', '')
                    }
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _combine_security_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine security analysis results into summary"""
        total_vulnerabilities = 0
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        tools_used = []
        
        for tool_name in ['bandit', 'codeql']:
            tool_result = results.get(tool_name)
            if tool_result and 'vulnerabilities' in tool_result:
                tools_used.append(tool_name)
                for vuln in tool_result['vulnerabilities']:
                    total_vulnerabilities += 1
                    severity = vuln.get('severity', 'info').lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    else:
                        severity_counts['info'] += 1
        
        return {
            "totalVulnerabilities": total_vulnerabilities,
            "severityBreakdown": severity_counts,
            "toolsUsed": tools_used,
            "riskLevel": self._calculate_risk_level(severity_counts)
        }
    
    def _calculate_risk_level(self, severity_counts: Dict[str, int]) -> str:
        """Calculate overall risk level"""
        if severity_counts['high'] > 0:
            return "HIGH"
        elif severity_counts['medium'] > 2:
            return "MEDIUM"
        elif severity_counts['low'] > 5:
            return "LOW"
        else:
            return "MINIMAL"