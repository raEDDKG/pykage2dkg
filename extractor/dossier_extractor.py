# extractor/dossier_extractor.py
import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List

class DossierExtractor:
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'typescript', 'rust', 'go']
    
    def extract_documentation(self, project_path: str, language: str = 'python') -> Dict[str, Any]:
        """Extract documentation using Dossier"""
        if language not in self.supported_languages:
            return {"error": f"Language {language} not supported by Dossier"}
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            # Run dossier command
            cmd = ['dossier', 'extract', '--format', 'json', '--output', tmp_path, project_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(tmp_path):
                with open(tmp_path, 'r') as f:
                    dossier_data = json.load(f)
                
                # Transform to our schema
                return self._transform_dossier_output(dossier_data, language)
            else:
                return {"error": f"Dossier failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Dossier extraction timed out"}
        except Exception as e:
            return {"error": f"Dossier extraction failed: {str(e)}"}
        finally:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _transform_dossier_output(self, dossier_data: Dict, language: str) -> Dict[str, Any]:
        """Transform Dossier output to our JSON-LD schema"""
        return {
            "@type": "DocumentationExtract",
            "language": language,
            "modules": self._extract_modules(dossier_data),
            "apiEndpoints": self._extract_api_endpoints(dossier_data),
            "documentation": self._extract_docs(dossier_data)
        }
    
    def _extract_modules(self, data: Dict) -> List[Dict[str, Any]]:
        modules = data.get('modules', [])
        return [{
            "@type": "DocumentedModule",
            "name": mod.get('name', ''),
            "description": mod.get('description', ''),
            "functions": mod.get('functions', []),
            "classes": mod.get('classes', [])
        } for mod in modules]
    
    def _extract_api_endpoints(self, data: Dict) -> List[Dict[str, Any]]:
        endpoints = data.get('api_endpoints', [])
        return [{
            "@type": "APIEndpoint",
            "path": ep.get('path', ''),
            "method": ep.get('method', ''),
            "description": ep.get('description', ''),
            "parameters": ep.get('parameters', [])
        } for ep in endpoints]
    
    def _extract_docs(self, data: Dict) -> Dict[str, Any]:
        return {
            "readme": data.get('readme', ''),
            "changelog": data.get('changelog', ''),
            "apiDocs": data.get('api_documentation', '')
        }