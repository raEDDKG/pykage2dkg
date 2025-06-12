#!/usr/bin/env python3
"""
Ecosystem Main - Clean CLI for temporary virtual environment analysis

Usage:
    python ecosystem_main.py "pip install emoji" --name emoji
    python ecosystem_main.py "uv add requests" --name requests
    python ecosystem_main.py "pip install 'fastapi[all]'" --name fastapi

Features:
- Creates temporary virtual environment
- Supports both pip and uv
- Complete isolation from current environment
- Automatic cleanup after analysis
- Generates separate JSON-LD files per package
- Master index for AI agent discovery
"""

import argparse
import tempfile
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import venv

class TemporaryEcosystemAnalyzer:
    """Analyzes package ecosystems in temporary, isolated environments"""
    
    def __init__(self, use_uv: bool = False):
        self.use_uv = use_uv
        self.temp_dir = None
        self.venv_path = None
        self.output_dir = Path("output_ecosystem")
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    def analyze_from_install_command(self, install_command: str, package_name: str) -> Dict[str, Any]:
        """
        Analyze ecosystem from install command in temporary environment
        
        Args:
            install_command: e.g., "pip install emoji" or "uv add requests"
            package_name: Primary package name for naming outputs
        """
        
        print(f"🌍 Analyzing ecosystem for: {package_name}")
        print(f"📦 Install command: {install_command}")
        print()
        
        # Use temporary directory with automatic cleanup
        with tempfile.TemporaryDirectory(prefix=f"ecosystem_{package_name}_") as temp_dir:
            self.temp_dir = temp_dir
            self.venv_path = os.path.join(temp_dir, "analysis_env")
            
            try:
                # Create isolated environment
                self._create_isolated_environment()
                
                # Parse and execute install command
                installed_packages = self._execute_install_command(install_command)
                
                # Analyze all packages in ecosystem
                ecosystem_analysis = self._analyze_ecosystem(installed_packages)
                
                # Generate outputs
                outputs = self._generate_outputs(package_name, ecosystem_analysis, install_command)
                
                print(f"✅ Analysis complete! Generated {len(outputs)} files")
                return outputs
                
            except Exception as e:
                print(f"❌ Error during analysis: {e}")
                raise
            
            # Cleanup happens automatically when exiting the context manager
    
    def _create_isolated_environment(self):
        """Create completely isolated virtual environment"""
        print(f"📁 Creating temporary environment: {self.venv_path}")
        
        if self.use_uv:
            # Create UV project
            subprocess.run([
                "uv", "init", "--no-readme", "--no-workspace", self.venv_path
            ], check=True, capture_output=True)
        else:
            # Create standard venv
            venv.create(self.venv_path, with_pip=True)
    
    def _execute_install_command(self, install_command: str) -> List[Dict[str, Any]]:
        """Parse and execute the install command"""
        
        # Get executable paths
        if self.use_uv:
            # UV uses project-based environments
            python_path = shutil.which("python") or sys.executable
            install_executable = "uv"
        else:
            if sys.platform == "win32":
                python_path = os.path.join(self.venv_path, "Scripts", "python")
                pip_path = os.path.join(self.venv_path, "Scripts", "pip")
            else:
                python_path = os.path.join(self.venv_path, "bin", "python")
                pip_path = os.path.join(self.venv_path, "bin", "pip")
            install_executable = pip_path
        
        # Parse install command
        command_parts = install_command.split()
        
        if self.use_uv:
            # Convert pip install to uv add
            if "pip install" in install_command:
                package_spec = " ".join(command_parts[2:])  # Everything after "pip install"
                cmd = ["uv", "add", package_spec]
            else:
                cmd = command_parts  # Assume it's already a uv command
            
            # Change to UV project directory
            original_cwd = os.getcwd()
            os.chdir(self.venv_path)
        else:
            # Use pip directly
            if command_parts[0] == "pip":
                cmd = [install_executable] + command_parts[1:]
            else:
                cmd = [install_executable, "install"] + command_parts
        
        print(f"🔧 Executing: {' '.join(cmd)}")
        
        try:
            # Execute install command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,
                cwd=self.venv_path if self.use_uv else None
            )
            
            if result.returncode != 0:
                print(f"⚠️ Install stderr: {result.stderr}")
                raise Exception(f"Install failed: {result.stderr}")
            
            print(f"✅ Installation successful")
            
            # Get list of installed packages
            if self.use_uv:
                # UV list packages
                list_cmd = ["uv", "pip", "list", "--format=json"]
                list_result = subprocess.run(
                    list_cmd, 
                    capture_output=True, 
                    text=True,
                    cwd=self.venv_path
                )
            else:
                # Pip list packages
                list_result = subprocess.run(
                    [install_executable, "list", "--format=json"], 
                    capture_output=True, 
                    text=True
                )
            
            if list_result.returncode == 0:
                installed = json.loads(list_result.stdout)
                print(f"📋 Installed {len(installed)} packages")
                return installed
            else:
                print(f"⚠️ Could not list packages: {list_result.stderr}")
                return []
                
        finally:
            if self.use_uv:
                os.chdir(original_cwd)
    
    def _analyze_ecosystem(self, installed_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all packages in the ecosystem"""
        
        # Get site-packages directory
        if self.use_uv:
            # UV stores packages in project .venv
            site_packages_path = os.path.join(self.venv_path, ".venv", "lib", "python3.12", "site-packages")
            python_path = os.path.join(self.venv_path, ".venv", "bin", "python")
        else:
            if sys.platform == "win32":
                python_path = os.path.join(self.venv_path, "Scripts", "python")
                site_packages_path = os.path.join(self.venv_path, "Lib", "site-packages")
            else:
                python_path = os.path.join(self.venv_path, "bin", "python")
                site_packages_path = os.path.join(self.venv_path, "lib", "python3.12", "site-packages")
        
        # Fallback: ask Python for site-packages
        if not os.path.exists(site_packages_path):
            try:
                site_result = subprocess.run([
                    python_path, "-c", 
                    "import site; print(site.getsitepackages()[0])"
                ], capture_output=True, text=True)
                if site_result.returncode == 0:
                    site_packages_path = site_result.stdout.strip()
            except:
                pass
        
        print(f"📂 Analyzing packages in: {site_packages_path}")
        
        ecosystem_analysis = {}
        
        # Analyze each package
        for package_info in installed_packages:
            package_name = package_info["name"]
            
            # Skip system packages
            if package_name.lower() in ["pip", "setuptools", "wheel", "uv"]:
                continue
            
            print(f"🔍 Analyzing: {package_name}")
            
            # Find package directory
            package_paths = self._find_package_paths(site_packages_path, package_name)
            
            if package_paths:
                # Analyze using our import validator
                analysis = self._analyze_package_imports(
                    package_paths[0], package_name, python_path
                )
                
                ecosystem_analysis[package_name] = {
                    "version": package_info["version"],
                    "paths": package_paths,
                    "analysis": analysis
                }
            else:
                print(f"⚠️ Could not find package directory for {package_name}")
        
        return ecosystem_analysis
    
    def _find_package_paths(self, site_packages_path: str, package_name: str) -> List[str]:
        """Find package directories in site-packages"""
        if not os.path.exists(site_packages_path):
            return []
        
        paths = []
        possible_names = [
            package_name,
            package_name.replace("-", "_"),
            package_name.replace("_", "-"),
            package_name.lower(),
            package_name.lower().replace("-", "_")
        ]
        
        for name in possible_names:
            package_dir = os.path.join(site_packages_path, name)
            if os.path.isdir(package_dir):
                paths.append(package_dir)
                break
        
        return paths
    
    def _analyze_package_imports(self, package_path: str, package_name: str, python_path: str) -> Dict[str, Any]:
        """Analyze imports for a single package using enhanced validator"""
        try:
            # Import the enhanced validator
            import sys
            import os
            
            # Add the current directory to Python path to import our modules
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            from extractor.enhanced_import_validator import EnhancedImportValidator
            
            # Use the enhanced validator that works in virtual environments
            validator = EnhancedImportValidator(python_path)
            validation_results = validator.validate_package_imports_in_venv(
                package_path, package_name, python_path
            )
            
            # Count Python files for additional context
            python_files = []
            if os.path.isdir(package_path):
                for root, dirs, files in os.walk(package_path):
                    for file in files:
                        if file.endswith('.py'):
                            python_files.append(os.path.join(root, file))
            
            return {
                "importValidation": validation_results,
                "fileCount": len(python_files),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "importValidation": {},
                "status": "failed",
                "error": str(e)
            }
    
    def _generate_outputs(self, primary_package: str, ecosystem_analysis: Dict[str, Any], install_command: str) -> Dict[str, str]:
        """Generate output files for AI agents"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        outputs = {}
        
        # 1. Generate individual package JSON-LD files
        for package_name, package_data in ecosystem_analysis.items():
            package_jsonld = self._create_package_jsonld(
                package_name, package_data, primary_package, install_command
            )
            
            filename = f"{package_name}_{timestamp}.jsonld"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(package_jsonld, f, indent=2)
            
            outputs[package_name] = str(filepath)
            print(f"📄 Generated: {filename}")
        
        # 2. Generate ecosystem master index
        master_index = self._create_master_index(
            primary_package, ecosystem_analysis, install_command, timestamp, outputs
        )
        
        master_filename = f"ecosystem_{primary_package}_{timestamp}.jsonld"
        master_filepath = self.output_dir / master_filename
        
        with open(master_filepath, 'w') as f:
            json.dump(master_index, f, indent=2)
        
        outputs["_master_index"] = str(master_filepath)
        print(f"📋 Generated master index: {master_filename}")
        
        return outputs
    
    def _create_package_jsonld(self, package_name: str, package_data: Dict[str, Any], 
                              primary_package: str, install_command: str) -> Dict[str, Any]:
        """Create JSON-LD for individual package"""
        
        return {
            "@context": [
                "https://schema.org",
                {
                    "analysis": "https://pykage2dkg.org/analysis#",
                    "ecosystem": "https://pykage2dkg.org/ecosystem#"
                }
            ],
            "@type": "SoftwareSourceCode",
            "name": package_name,
            "version": package_data["version"],
            "programmingLanguage": "Python",
            "isPartOfEcosystem": primary_package,
            "installCommand": install_command,
            "analysisMetadata": {
                "@type": "PackageAnalysis",
                "timestamp": datetime.utcnow().isoformat(),
                "analysisType": "ecosystem_member",
                "status": package_data["analysis"]["status"]
            },
            "importValidation": package_data["analysis"]["importValidation"],
            "aiAgentGuidance": {
                "@type": "AIAgentGuidance",
                "packageRole": "primary" if package_name == primary_package else "dependency",
                "safeImports": self._extract_safe_imports(package_data["analysis"]),
                "installationContext": {
                    "requiresEcosystem": True,
                    "installCommand": install_command,
                    "primaryPackage": primary_package
                }
            }
        }
    
    def _create_master_index(self, primary_package: str, ecosystem_analysis: Dict[str, Any], 
                           install_command: str, timestamp: str, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Create master ecosystem index for AI agents"""
        
        return {
            "@context": [
                "https://schema.org",
                {
                    "ecosystem": "https://pykage2dkg.org/ecosystem#"
                }
            ],
            "@type": "SoftwareEcosystem",
            "name": f"{primary_package}_ecosystem",
            "primaryPackage": primary_package,
            "installCommand": install_command,
            "analysisMetadata": {
                "@type": "EcosystemAnalysis",
                "timestamp": datetime.utcnow().isoformat(),
                "totalPackages": len(ecosystem_analysis),
                "analysisApproach": "temporary_isolated_environment"
            },
            "packageMembers": [
                {
                    "name": package_name,
                    "version": package_data["version"],
                    "role": "primary" if package_name == primary_package else "dependency",
                    "analysisFile": outputs.get(package_name, ""),
                    "status": package_data["analysis"]["status"]
                }
                for package_name, package_data in ecosystem_analysis.items()
            ],
            "aiAgentGuidance": {
                "@type": "EcosystemGuidance",
                "quickStart": {
                    "installCommand": install_command,
                    "primaryImports": self._get_primary_imports(ecosystem_analysis, primary_package),
                    "dependencyChain": list(ecosystem_analysis.keys())
                },
                "individualPackageAnalyses": {
                    package_name: outputs.get(package_name, "")
                    for package_name in ecosystem_analysis.keys()
                }
            }
        }
    
    def _extract_safe_imports(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract safe imports from analysis"""
        if analysis["status"] != "success":
            return []
        
        valid_imports = analysis["importValidation"].get("validatedImports", {})
        return [
            {
                "importPath": import_info["importPath"],
                "verified": True,
                "type": import_info.get("exportType", "unknown")
            }
            for import_path, import_info in valid_imports.items()
        ]
    
    def _get_primary_imports(self, ecosystem_analysis: Dict[str, Any], primary_package: str) -> List[str]:
        """Get primary imports for the main package"""
        if primary_package not in ecosystem_analysis:
            return []
        
        analysis = ecosystem_analysis[primary_package]["analysis"]
        if analysis["status"] != "success":
            return []
        
        valid_imports = analysis["importValidation"].get("validatedImports", {})
        return [
            import_info["importPath"]
            for import_info in valid_imports.values()
        ][:5]  # Top 5 imports

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Analyze Python package ecosystems in temporary isolated environments"
    )
    parser.add_argument(
        "install_command",
        help='Install command in quotes, e.g., "pip install emoji" or "uv add requests"'
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Primary package name for output naming"
    )
    parser.add_argument(
        "--use-uv",
        action="store_true",
        help="Use UV instead of pip (experimental)"
    )
    
    args = parser.parse_args()
    
    print("🚀 TEMPORARY ECOSYSTEM ANALYZER")
    print("=" * 40)
    print()
    
    analyzer = TemporaryEcosystemAnalyzer(use_uv=args.use_uv)
    
    try:
        outputs = analyzer.analyze_from_install_command(
            args.install_command, 
            args.name
        )
        
        print()
        print("🎉 SUCCESS! Generated files:")
        for package, filepath in outputs.items():
            print(f"   📄 {package}: {filepath}")
        
        print()
        print("🤖 AI agents can now:")
        print("   • Load individual package analyses")
        print("   • Understand complete ecosystem dependencies")
        print("   • Get verified import statements")
        print("   • Know exact installation requirements")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()