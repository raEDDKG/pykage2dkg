#!/usr/bin/env python3
"""
Enhanced Ecosystem Main - AI Agent Optimized Analysis

Key Improvements:
1. Support both install commands AND directory paths
2. Focus deep analysis on PRIMARY package only
3. Install dependencies for import validation but don't deep analyze them
4. Use sentence-transformers for AI compatibility
5. Configurable embeddings with metadata
6. Enhanced metadata extraction from source repositories

Usage:
    # Install command (installs dependencies + analyzes primary)
    python enhanced_ecosystem_main.py "pip install requests" --name requests
    
    # Directory path (installs dependencies + analyzes local directory)
    python enhanced_ecosystem_main.py /path/to/package --name mypackage --install-deps "requests urllib3"
    
    # With embedding options
    python enhanced_ecosystem_main.py "pip install fastapi" --name fastapi --embedding-model sentence-transformers/all-MiniLM-L6-v2
"""

import argparse
import tempfile
import subprocess
import sys
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import venv

# Import our existing components
from ecosystem_main import TemporaryEcosystemAnalyzer
from extractor.codemeta_wrapper import extract_codemeta
from extractor.hierarchical_walker import walk_python_modules_enhanced
from extractor.converter import convert_to_enhanced_jsonld
from extractor.runtime_extractor import extract_runtime_behavior
from extractor.enhanced_import_validator import enhance_with_enhanced_import_validation
from extractor.ai_embeddings import enhance_jsonld_with_ai_embeddings

class EnhancedEcosystemAnalyzer:
    """AI Agent optimized ecosystem analyzer"""
    
    def __init__(self, use_uv: bool = False, embedding_model: Optional[str] = None):
        self.use_uv = use_uv                        # microsoft/codebert-base too slow
        self.embedding_model = embedding_model or "neulab/codebert-python"
        self.temp_dir = None
        self.venv_path = None
        self.ecosystem_output_dir = Path("output_ecosystem")
        self.deep_output_dir = Path("output_jsonld")
        
        # Ensure output directories exist
        self.ecosystem_output_dir.mkdir(exist_ok=True)
        self.deep_output_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model if available
        self.embedder = self._initialize_embedder()
    
    def _initialize_embedder(self) -> Optional[Any]:
        """Initialize code-focused embedder if available"""
        try:
            # Try to use our AI embeddings module with CodeBERT
            from extractor.ai_embeddings import AIEmbeddingGenerator
            print(f"🤖 Initializing code embedding model: {self.embedding_model}")
            return AIEmbeddingGenerator(self.embedding_model)
        except ImportError as e:
            print(f"⚠️ AI embeddings module not available: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Failed to load code embedding model {self.embedding_model}: {e}")
            return None
    
    def analyze_package_focused(self, source: str, package_name: str, 
                               install_deps: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze package with focus on primary package only
        
        Args:
            source: Install command (e.g., "pip install requests") OR directory path
            package_name: Primary package name
            install_deps: Optional dependency install command for directory analysis
        """
        
        print("🚀 ENHANCED ECOSYSTEM ANALYZER - AI AGENT OPTIMIZED")
        print("=" * 55)
        print(f"🎯 Primary Package: {package_name}")
        print(f"📦 Source: {source}")
        if install_deps:
            print(f"📋 Dependencies: {install_deps}")
        print(f"🤖 Embedding Model: {self.embedding_model}")
        print()
        
        # Determine if source is install command or directory path
        is_directory = os.path.isdir(source)
        
        # Use temporary directory with automatic cleanup
        with tempfile.TemporaryDirectory(prefix=f"enhanced_{package_name}_") as temp_dir:
            self.temp_dir = temp_dir
            self.venv_path = os.path.join(temp_dir, "analysis_env")
            
            try:
                if is_directory:
                    # DIRECTORY PATH MODE
                    print("📁 DIRECTORY PATH MODE")
                    print("-" * 25)
                    results = self._analyze_directory_with_deps(source, package_name, install_deps)
                else:
                    # INSTALL COMMAND MODE  
                    print("📦 INSTALL COMMAND MODE")
                    print("-" * 25)
                    results = self._analyze_install_command_focused(source, package_name)
                
                print(f"\n✅ ENHANCED ANALYSIS COMPLETE!")
                print(f"🎯 Primary package deep analysis: ✅")
                print(f"📊 Dependencies analyzed for imports: ✅")
                print(f"🤖 AI agent optimized output: ✅")
                
                return results
                
            except Exception as e:
                print(f"❌ Error during enhanced analysis: {e}")
                raise
    
    def _analyze_directory_with_deps(self, directory_path: str, package_name: str, 
                                   install_deps: Optional[str]) -> Dict[str, Any]:
        """Analyze local directory but install dependencies for import validation"""
        
        # Step 1: Create isolated environment
        print("🏗️ Creating isolated environment...")
        self._create_isolated_environment()
        
        # Step 2: Install dependencies if specified
        dependency_info = {}
        if install_deps:
            print(f"📦 Installing dependencies: {install_deps}")
            dependency_info = self._install_dependencies(install_deps)
        
        # Step 3: Deep analyze the primary package (local directory)
        print(f"🔬 Deep analyzing primary package: {package_name}")
        primary_analysis = self._deep_analyze_package(directory_path, package_name)
        
        # Step 4: Light analyze dependencies for import context
        print("📋 Light analyzing dependencies for import context...")
        dependency_analyses = self._light_analyze_dependencies(dependency_info)
        
        # Step 5: Generate enhanced outputs
        print("📄 Generating AI-optimized outputs...")
        outputs = self._generate_enhanced_outputs(
            package_name, primary_analysis, dependency_analyses, 
            source_type="directory", source_path=directory_path
        )
        
        return outputs
    
    def _analyze_install_command_focused(self, install_command: str, package_name: str) -> Dict[str, Any]:
        """Analyze install command but focus deep analysis on primary package only"""
        
        # Step 1: Create isolated environment and install ecosystem
        print("🏗️ Creating isolated environment...")
        self._create_isolated_environment()
        
        print(f"📦 Installing ecosystem: {install_command}")
        installed_packages = self._execute_install_command(install_command)
        
        # Step 2: Find primary package path
        primary_package_path = self._find_primary_package_path(package_name)
        if not primary_package_path:
            raise ValueError(f"Could not find primary package '{package_name}' after installation")
        
        # Step 3: Deep analyze ONLY the primary package
        print(f"🔬 Deep analyzing primary package: {package_name}")
        primary_analysis = self._deep_analyze_package(primary_package_path, package_name)
        
        # Step 4: Light analyze dependencies for import context
        print("📋 Light analyzing dependencies for import context...")
        dependency_analyses = self._light_analyze_dependencies_from_installed(
            installed_packages, package_name
        )
        
        # Step 5: Generate enhanced outputs
        print("📄 Generating AI-optimized outputs...")
        outputs = self._generate_enhanced_outputs(
            package_name, primary_analysis, dependency_analyses,
            source_type="install", install_command=install_command
        )
        
        return outputs
    
    def _create_isolated_environment(self):
        """Create isolated virtual environment"""
        print(f"📁 Environment: {self.venv_path}")
        
        if self.use_uv:
            subprocess.run([
                "uv", "init", "--no-readme", "--no-workspace", self.venv_path
            ], check=True, capture_output=True)
        else:
            venv.create(self.venv_path, with_pip=True)
    
    def _install_dependencies(self, install_deps: str) -> Dict[str, Any]:
        """Install dependencies and return info about them"""
        
        # Get executable paths
        python_path, pip_path = self._get_executable_paths()
        
        # Parse install command
        if install_deps.startswith("pip install"):
            command_parts = install_deps.split()[2:]  # Remove "pip install"
        else:
            command_parts = install_deps.split()
        
        # Execute install
        cmd = [pip_path, "install"] + command_parts
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Dependency installation failed: {result.stderr}")
        
        # Get list of installed packages
        list_result = subprocess.run([pip_path, "list", "--format=json"], 
                                   capture_output=True, text=True)
        installed = json.loads(list_result.stdout) if list_result.returncode == 0 else []
        
        return {
            "installed_packages": installed,
            "install_command": install_deps
        }
    
    def _execute_install_command(self, install_command: str) -> List[Dict[str, Any]]:
        """Execute install command and return installed packages"""
        
        python_path, pip_path = self._get_executable_paths()
        
        # Parse install command
        if install_command.startswith("pip install"):
            command_parts = install_command.split()[2:]
        elif install_command.startswith("uv add"):
            command_parts = install_command.split()[2:]
        else:
            raise ValueError(f"Unsupported install command: {install_command}")
        
        # Execute install
        if self.use_uv:
            cmd = ["uv", "add"] + command_parts
        else:
            cmd = [pip_path, "install"] + command_parts
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"Installation failed: {result.stderr}")
        
        # Get installed packages
        list_result = subprocess.run([pip_path, "list", "--format=json"],
                                   capture_output=True, text=True)
        return json.loads(list_result.stdout) if list_result.returncode == 0 else []
    
    def _get_executable_paths(self) -> tuple[str, str]:
        """Get Python and pip executable paths"""
        if self.use_uv:
            python_path = os.path.join(self.venv_path, ".venv", "bin", "python")
            pip_path = os.path.join(self.venv_path, ".venv", "bin", "pip")
        else:
            if sys.platform == "win32":
                python_path = os.path.join(self.venv_path, "Scripts", "python")
                pip_path = os.path.join(self.venv_path, "Scripts", "pip")
            else:
                python_path = os.path.join(self.venv_path, "bin", "python")
                pip_path = os.path.join(self.venv_path, "bin", "pip")
        
        return python_path, pip_path
    
    def _find_primary_package_path(self, package_name: str) -> Optional[str]:
        """Find the primary package path in site-packages"""
        site_packages_path = self._get_site_packages_path()
        
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
                return package_dir
        
        return None
    
    def _get_site_packages_path(self) -> str:
        """Get site-packages path"""
        python_path, _ = self._get_executable_paths()
        
        try:
            site_result = subprocess.run([
                python_path, "-c", 
                "import site; print(site.getsitepackages()[0])"
            ], capture_output=True, text=True)
            if site_result.returncode == 0:
                return site_result.stdout.strip()
        except:
            pass
        
        # Fallback
        if self.use_uv:
            return os.path.join(self.venv_path, ".venv", "lib", "python3.12", "site-packages")
        else:
            if sys.platform == "win32":
                return os.path.join(self.venv_path, "Lib", "site-packages")
            else:
                return os.path.join(self.venv_path, "lib", "python3.12", "site-packages")
    
    def _deep_analyze_package(self, package_path: str, package_name: str) -> Dict[str, Any]:
        """Perform deep analysis on a single package (the main.py pipeline)"""
        
        try:
            # Extract codemeta metadata with enhanced source repository info
            meta = self._extract_enhanced_metadata(package_path, package_name)
            
            # Walk Python modules with enhanced analysis
            modules = walk_python_modules_enhanced(package_path)
            
            # Extract runtime behavior
            runtime = extract_runtime_behavior(package_path)
            
            # Convert to enhanced JSON-LD
            jsonld = convert_to_enhanced_jsonld(meta, modules, package_name, runtime, package_path)
            
            # Add enhanced import validation
            python_executable, _ = self._get_executable_paths()
            jsonld = enhance_with_enhanced_import_validation(
                jsonld, package_path, package_name, python_executable
            )
            
            # Add AI-optimized embeddings
            jsonld = self._add_ai_optimized_embeddings(jsonld, package_name)
            
            return {
                "jsonld": jsonld,
                "metadata": meta,
                "modules": modules,
                "runtime": runtime,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "jsonld": None,
                "status": "failed",
                "error": str(e)
            }
    
    def _extract_enhanced_metadata(self, package_path: str, package_name: str) -> Dict[str, Any]:
        """Extract metadata with enhanced source repository information"""
        
        # Start with basic codemeta extraction
        meta = extract_codemeta(package_path, package_name)
        
        # Try to enhance with source repository info
        try:
            repo_info = self._fetch_repository_metadata(package_name)
            if repo_info:
                meta.update(repo_info)
        except Exception as e:
            print(f"⚠️ Could not fetch repository metadata: {e}")
        
        return meta
    
    def _fetch_repository_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch enhanced metadata from source repositories"""
        
        try:
            import requests
            
            # Try PyPI API first
            pypi_url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(pypi_url, timeout=10)
            
            if response.status_code == 200:
                pypi_data = response.json()
                info = pypi_data.get("info", {})
                
                enhanced_meta = {}
                
                # Add repository URLs
                if info.get("home_page"):
                    enhanced_meta["codeRepository"] = info["home_page"]
                if info.get("project_urls"):
                    enhanced_meta["projectUrls"] = info["project_urls"]
                
                # Add enhanced description
                if info.get("summary"):
                    enhanced_meta["description"] = info["summary"]
                
                # Add keywords
                if info.get("keywords"):
                    enhanced_meta["keywords"] = info["keywords"].split(",")
                
                # Add classifiers for AI context
                if info.get("classifiers"):
                    enhanced_meta["classifiers"] = info["classifiers"]
                
                return enhanced_meta
                
        except Exception:
            pass
        
        return None
    
    def _light_analyze_dependencies(self, dependency_info: Dict[str, Any]) -> Dict[str, Any]:
        """Light analysis of dependencies (just import validation, no deep analysis)"""
        
        dependency_analyses = {}
        installed_packages = dependency_info.get("installed_packages", [])
        
        for package_info in installed_packages:
            package_name = package_info["name"]
            
            # Skip common system packages
            if package_name.lower() in ["pip", "setuptools", "wheel"]:
                continue
            
            print(f"📋 Light analyzing: {package_name}")
            
            try:
                # Just do import validation, no deep analysis
                python_executable, _ = self._get_executable_paths()
                package_path = self._find_primary_package_path(package_name)
                
                if package_path:
                    from extractor.enhanced_import_validator import EnhancedImportValidator
                    validator = EnhancedImportValidator(python_executable)
                    validation_results = validator.validate_package_imports_in_venv(
                        package_path, package_name, python_executable
                    )
                    
                    dependency_analyses[package_name] = {
                        "version": package_info.get("version", "unknown"),
                        "importValidation": validation_results,
                        "analysisType": "light",
                        "status": "success"
                    }
                else:
                    dependency_analyses[package_name] = {
                        "version": package_info.get("version", "unknown"),
                        "status": "path_not_found"
                    }
                    
            except Exception as e:
                dependency_analyses[package_name] = {
                    "version": package_info.get("version", "unknown"),
                    "status": "failed",
                    "error": str(e)
                }
        
        return dependency_analyses
    
    def _light_analyze_dependencies_from_installed(self, installed_packages: List[Dict[str, Any]], 
                                                  primary_package: str) -> Dict[str, Any]:
        """Light analyze dependencies from installed package list"""
        
        # Filter out the primary package
        dependencies = [pkg for pkg in installed_packages if pkg["name"] != primary_package]
        
        return self._light_analyze_dependencies({"installed_packages": dependencies})
    
    def _add_ai_optimized_embeddings(self, jsonld: Dict[str, Any], package_name: str) -> Dict[str, Any]:
        """Add AI-optimized embeddings using the enhanced embedding module"""
        
        # Use the enhanced AI embeddings module
        embedding_formats = ["codebert", "list"]  # Multiple formats for compatibility
        
        try:
            enhanced_jsonld = enhance_jsonld_with_ai_embeddings(
                jsonld, 
                embedding_model=self.embedding_model,
                formats=embedding_formats
            )
            return enhanced_jsonld
            
        except Exception as e:
            # Fallback: add basic embedding metadata
            jsonld["aiEmbeddings"] = {
                "@type": "AIEmbeddings",
                "status": "failed",
                "error": str(e),
                "metadata": {
                    "@type": "EmbeddingMetadata",
                    "status": "not_available",
                    "reason": f"Embedding generation failed: {str(e)}",
                    "recommendedModel": self.embedding_model,
                    "aiAgentNote": "AI agents can generate their own embeddings using the text content",
                    "aiCompatibility": {
                        "recommendation": "Install sentence-transformers for proper embeddings",
                        "alternatives": [
                            "Use OpenAI embeddings API",
                            "Use Hugging Face transformers", 
                            "Generate embeddings client-side"
                        ]
                    }
                }
            }
            return jsonld
    
    def _generate_enhanced_outputs(self, package_name: str, primary_analysis: Dict[str, Any],
                                 dependency_analyses: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate AI-optimized outputs"""
        
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        outputs = {}
        
        # Generate primary package deep analysis file
        if primary_analysis["status"] == "success":
            primary_filename = f"{package_name}_ai_optimized_{timestamp}.jsonld"
            primary_filepath = self.deep_output_dir / primary_filename
            
            with open(primary_filepath, 'w', encoding='utf-8') as f:
                json.dump(primary_analysis["jsonld"], f, indent=2)
            
            outputs["primary_package"] = str(primary_filepath)
        
        # Generate ecosystem overview with light dependency info
        ecosystem_overview = {
            "@context": ["https://schema.org"],
            "@type": "AIOptimizedEcosystem",
            "primaryPackage": package_name,
            "analysisTimestamp": timestamp,
            "analysisApproach": "ai_agent_focused",
            "embeddingModel": self.embedding_model,
            "sourceType": kwargs.get("source_type", "unknown"),
            "primaryPackageAnalysis": {
                "status": primary_analysis["status"],
                "deepAnalysis": primary_analysis["status"] == "success",
                "file": primary_filename if primary_analysis["status"] == "success" else None
            },
            "dependencies": {},
            "aiAgentGuidance": {
                "@type": "AIAgentEcosystemGuidance",
                "focus": "Primary package has complete deep analysis, dependencies have import validation only",
                "recommendation": "Use primary package analysis for detailed code understanding",
                "embeddingCompatibility": "sentence-transformers format for universal AI agent compatibility"
            }
        }
        
        # Add dependency info (light analysis only)
        for dep_name, dep_analysis in dependency_analyses.items():
            ecosystem_overview["dependencies"][dep_name] = {
                "version": dep_analysis.get("version", "unknown"),
                "analysisType": "light_import_validation_only",
                "importValidation": dep_analysis.get("importValidation", {}),
                "status": dep_analysis.get("status", "unknown")
            }
        
        # Save ecosystem overview
        ecosystem_filename = f"ecosystem_{package_name}_ai_optimized_{timestamp}.jsonld"
        ecosystem_filepath = self.ecosystem_output_dir / ecosystem_filename
        
        with open(ecosystem_filepath, 'w', encoding='utf-8') as f:
            json.dump(ecosystem_overview, f, indent=2)
        
        outputs["ecosystem_overview"] = str(ecosystem_filepath)
        
        return outputs

def main():
    """Main CLI interface for enhanced ecosystem analysis"""
    parser = argparse.ArgumentParser(
        description="Enhanced ecosystem analysis optimized for AI agents"
    )
    parser.add_argument(
        "source",
        help='Install command in quotes (e.g., "pip install requests") OR directory path'
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Primary package name"
    )
    parser.add_argument(
        "--install-deps",
        help="Dependencies to install when using directory path (e.g., 'requests urllib3')"
    )
    parser.add_argument(
        "--use-uv",
        action="store_true",
        help="Use UV instead of pip"
    )
    parser.add_argument(
        "--embedding-model",
        # microsoft/codebert-base too slow
        default="neulab/codebert-python",
        help="Code-focused embedding model for AI-compatible embeddings"
    )
    
    args = parser.parse_args()
    
    analyzer = EnhancedEcosystemAnalyzer(
        use_uv=args.use_uv,
        embedding_model=args.embedding_model
    )
    
    try:
        results = analyzer.analyze_package_focused(
            args.source,
            args.name,
            args.install_deps
        )
        
        print("\n🎉 AI-OPTIMIZED ANALYSIS COMPLETE!")
        print("=" * 40)
        print(f"🎯 Primary package: Deep analysis ✅")
        print(f"📋 Dependencies: Import validation ✅")
        print(f"🤖 AI compatibility: Optimized ✅")
        print(f"📊 Embedding model: {args.embedding_model}")
        print()
        print("📂 Generated files:")
        for key, filepath in results.items():
            print(f"   📄 {key}: {filepath}")
        
    except Exception as e:
        print(f"❌ Enhanced analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()