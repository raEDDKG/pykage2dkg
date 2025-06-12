#!/usr/bin/env python3
"""
Ecosystem Analyzer - Complete Package Ecosystem Analysis

Instead of analyzing one package, this analyzes the ENTIRE pip install ecosystem:
- All dependencies and their dependencies
- Cross-package import relationships  
- Complete dependency tree understanding
- Platform-specific and optional dependency handling

This gives AI agents a COMPLETE picture of how Python packages work together.
"""

import subprocess
import tempfile
import os
import sys
import json
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
import venv

class EcosystemAnalyzer:
    """Analyzes complete package ecosystems via pip install"""
    
    def __init__(self):
        self.temp_dir = None
        self.venv_path = None
        self.analysis_results = {}
        
    def analyze_package_ecosystem(self, package_name: str, include_extras: bool = True) -> Dict[str, Any]:
        """
        Analyze complete ecosystem for a package by:
        1. Creating isolated virtual environment
        2. Installing package + all dependencies
        3. Analyzing all installed packages
        4. Mapping cross-package relationships
        """
        
        print(f"🌍 Analyzing complete ecosystem for: {package_name}")
        
        try:
            # Create isolated environment
            self._create_isolated_environment()
            
            # Install package with all dependencies
            installed_packages = self._install_package_ecosystem(package_name, include_extras)
            
            # Analyze all packages in the ecosystem
            ecosystem_analysis = self._analyze_all_packages(installed_packages)
            
            # Map cross-package relationships
            relationship_map = self._map_package_relationships(ecosystem_analysis)
            
            # Generate AI agent guidance for the entire ecosystem
            ai_guidance = self._generate_ecosystem_guidance(ecosystem_analysis, relationship_map)
            
            return {
                "targetPackage": package_name,
                "ecosystemAnalysis": {
                    "@type": "PackageEcosystem",
                    "installedPackages": installed_packages,
                    "packageAnalysis": ecosystem_analysis,
                    "crossPackageRelationships": relationship_map,
                    "aiAgentGuidance": ai_guidance
                }
            }
            
        finally:
            # Cleanup
            self._cleanup()
    
    def _create_isolated_environment(self):
        """Create isolated virtual environment for analysis"""
        self.temp_dir = tempfile.mkdtemp(prefix="ecosystem_analysis_")
        self.venv_path = os.path.join(self.temp_dir, "analysis_env")
        
        print(f"📁 Creating isolated environment: {self.venv_path}")
        venv.create(self.venv_path, with_pip=True)
    
    def _install_package_ecosystem(self, package_name: str, include_extras: bool) -> List[Dict[str, Any]]:
        """Install package and all dependencies, return what was installed"""
        
        # Get pip and python paths in virtual environment
        if sys.platform == "win32":
            pip_path = os.path.join(self.venv_path, "Scripts", "pip")
            python_path = os.path.join(self.venv_path, "Scripts", "python")
        else:
            pip_path = os.path.join(self.venv_path, "bin", "pip")
            python_path = os.path.join(self.venv_path, "bin", "python")
        
        # Install the package
        install_cmd = [pip_path, "install"]
        
        if include_extras:
            # Try to install with all extras
            try:
                print(f"📦 Installing {package_name} with all extras...")
                result = subprocess.run(
                    install_cmd + [f"{package_name}[all]"], 
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    print(f"⚠️ Failed to install with [all], trying without extras...")
                    result = subprocess.run(
                        install_cmd + [package_name], 
                        capture_output=True, text=True, timeout=300
                    )
            except subprocess.TimeoutExpired:
                print(f"⚠️ Installation timeout, trying without extras...")
                result = subprocess.run(
                    install_cmd + [package_name], 
                    capture_output=True, text=True, timeout=300
                )
        else:
            result = subprocess.run(
                install_cmd + [package_name], 
                capture_output=True, text=True, timeout=300
            )
        
        if result.returncode != 0:
            raise Exception(f"Failed to install {package_name}: {result.stderr}")
        
        # Get list of installed packages
        list_result = subprocess.run(
            [pip_path, "list", "--format=json"], 
            capture_output=True, text=True
        )
        
        if list_result.returncode == 0:
            installed = json.loads(list_result.stdout)
            print(f"✅ Installed {len(installed)} packages in ecosystem")
            return installed
        else:
            return []
    
    def _analyze_all_packages(self, installed_packages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all packages in the ecosystem"""
        
        # Get site-packages directory
        if sys.platform == "win32":
            python_path = os.path.join(self.venv_path, "Scripts", "python")
        else:
            python_path = os.path.join(self.venv_path, "bin", "python")
        
        # Get site-packages path
        site_packages_result = subprocess.run([
            python_path, "-c", 
            "import site; print(site.getsitepackages()[0])"
        ], capture_output=True, text=True)
        
        if site_packages_result.returncode != 0:
            raise Exception("Could not find site-packages directory")
        
        site_packages_path = site_packages_result.stdout.strip()
        print(f"📂 Analyzing packages in: {site_packages_path}")
        
        ecosystem_analysis = {}
        
        # Analyze each installed package
        for package_info in installed_packages:
            package_name = package_info["name"]
            package_version = package_info["version"]
            
            # Skip pip, setuptools, etc.
            if package_name.lower() in ["pip", "setuptools", "wheel"]:
                continue
            
            print(f"🔍 Analyzing package: {package_name}")
            
            # Find package directory
            package_paths = self._find_package_paths(site_packages_path, package_name)
            
            if package_paths:
                # Analyze the package using our existing tools
                package_analysis = self._analyze_single_package(
                    package_paths[0], package_name, python_path
                )
                
                ecosystem_analysis[package_name] = {
                    "version": package_version,
                    "paths": package_paths,
                    "analysis": package_analysis
                }
        
        return ecosystem_analysis
    
    def _find_package_paths(self, site_packages_path: str, package_name: str) -> List[str]:
        """Find all paths for a package in site-packages"""
        paths = []
        
        # Common package directory patterns
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
        
        return paths
    
    def _analyze_single_package(self, package_path: str, package_name: str, python_path: str) -> Dict[str, Any]:
        """Analyze a single package using our existing import validator"""
        
        # Set up environment to use the virtual environment's Python
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(package_path)
        
        try:
            # Use our existing import validator, but in the virtual environment context
            from extractor.import_validator import ImportValidator
            
            # Create validator instance
            validator = ImportValidator()
            
            # Validate imports for this package
            validation_results = validator.validate_package_imports(package_path, package_name)
            
            return {
                "importValidation": validation_results,
                "packagePath": package_path,
                "analysisStatus": "success"
            }
            
        except Exception as e:
            return {
                "importValidation": {},
                "packagePath": package_path,
                "analysisStatus": "failed",
                "error": str(e)
            }
    
    def _map_package_relationships(self, ecosystem_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Map relationships between packages in the ecosystem"""
        
        relationships = {
            "importDependencies": {},
            "crossPackageImports": {},
            "dependencyChains": {}
        }
        
        # Analyze cross-package imports
        for package_name, package_data in ecosystem_analysis.items():
            if "analysis" in package_data and "importValidation" in package_data["analysis"]:
                valid_imports = package_data["analysis"]["importValidation"].get("validatedImports", {})
                
                # Look for imports that reference other packages in the ecosystem
                cross_imports = []
                for import_path, import_info in valid_imports.items():
                    import_statement = import_info.get("importPath", "")
                    
                    # Check if this import references another package in our ecosystem
                    for other_package in ecosystem_analysis.keys():
                        if other_package != package_name and other_package in import_statement:
                            cross_imports.append({
                                "targetPackage": other_package,
                                "importStatement": import_statement,
                                "importPath": import_path
                            })
                
                if cross_imports:
                    relationships["crossPackageImports"][package_name] = cross_imports
        
        return relationships
    
    def _generate_ecosystem_guidance(self, ecosystem_analysis: Dict[str, Any], relationships: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI agent guidance for the entire ecosystem"""
        
        guidance = {
            "ecosystemOverview": {
                "totalPackages": len(ecosystem_analysis),
                "packagesWithValidation": len([p for p in ecosystem_analysis.values() 
                                             if p.get("analysis", {}).get("analysisStatus") == "success"]),
                "crossPackageRelationships": len(relationships.get("crossPackageImports", {}))
            },
            "recommendedInstallation": {},
            "safeImportPatterns": {},
            "ecosystemDependencies": relationships,
            "troubleshooting": {}
        }
        
        # Generate installation recommendations
        successful_packages = [name for name, data in ecosystem_analysis.items() 
                             if data.get("analysis", {}).get("analysisStatus") == "success"]
        
        guidance["recommendedInstallation"] = {
            "primaryCommand": f"pip install {' '.join(successful_packages[:5])}",  # Top 5
            "fullEcosystem": f"pip install {' '.join(successful_packages)}",
            "verifiedPackages": successful_packages
        }
        
        # Collect all safe imports across the ecosystem
        all_safe_imports = {}
        for package_name, package_data in ecosystem_analysis.items():
            if "analysis" in package_data and "importValidation" in package_data["analysis"]:
                valid_imports = package_data["analysis"]["importValidation"].get("validatedImports", {})
                for import_path, import_info in valid_imports.items():
                    all_safe_imports[import_path] = {
                        "package": package_name,
                        "importStatement": import_info.get("importPath", ""),
                        "verified": True
                    }
        
        guidance["safeImportPatterns"] = all_safe_imports
        
        return guidance
    
    def _cleanup(self):
        """Clean up temporary environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            print(f"🧹 Cleaning up: {self.temp_dir}")
            shutil.rmtree(self.temp_dir, ignore_errors=True)

def demo_ecosystem_analysis():
    """Demo the ecosystem analysis approach"""
    
    print("🌍 ECOSYSTEM ANALYSIS DEMO")
    print("=" * 40)
    print()
    
    analyzer = EcosystemAnalyzer()
    
    # Test with a smaller package first
    test_package = "requests"  # Popular package with dependencies
    
    try:
        results = analyzer.analyze_package_ecosystem(test_package, include_extras=False)
        
        print("📊 ECOSYSTEM ANALYSIS RESULTS:")
        print("-" * 30)
        
        ecosystem = results["ecosystemAnalysis"]
        
        print(f"🎯 Target Package: {results['targetPackage']}")
        print(f"📦 Total Packages Installed: {len(ecosystem['installedPackages'])}")
        print(f"🔍 Packages Analyzed: {len(ecosystem['packageAnalysis'])}")
        
        print("\n📋 Installed Packages:")
        for pkg in ecosystem['installedPackages'][:10]:  # Show first 10
            print(f"   • {pkg['name']} ({pkg['version']})")
        
        print(f"\n🔗 Cross-Package Relationships:")
        cross_imports = ecosystem['crossPackageRelationships'].get('crossPackageImports', {})
        for package, imports in cross_imports.items():
            print(f"   📦 {package} imports from:")
            for imp in imports[:3]:  # Show first 3
                print(f"      → {imp['targetPackage']}: {imp['importStatement']}")
        
        print(f"\n🤖 AI Agent Guidance:")
        guidance = ecosystem['aiAgentGuidance']
        print(f"   📊 Overview: {guidance['ecosystemOverview']}")
        print(f"   💾 Install Command: {guidance['recommendedInstallation']['primaryCommand']}")
        print(f"   ✅ Safe Imports: {len(guidance['safeImportPatterns'])} verified")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during ecosystem analysis: {e}")
        return None

if __name__ == "__main__":
    demo_ecosystem_analysis()