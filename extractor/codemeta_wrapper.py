# extractor/codemeta_wrapper.py

import subprocess
import json
import tempfile
import os
import shutil
import requests
from urllib.parse import quote_plus


def extract_pypi_metadata(package_name):
    """
    Fetch metadata from PyPI JSON API.
    Returns dict with schema.org metadata or empty dict on failure.
    """
    url = f"https://pypi.org/pypi/{quote_plus(package_name)}/json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        info = resp.json()["info"]
        
        # Extract project URLs for repository info
        project_urls = info.get("project_urls", {})
        repo_url = (
            info.get("home_page") or 
            project_urls.get("Homepage") or
            project_urls.get("Repository") or
            project_urls.get("Source") or
            project_urls.get("Source Code")
        )
        
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareSourceCode",
            "name": info.get("name", package_name),
            "version": info.get("version"),
            "description": info.get("summary"),
            "license": info.get("license"),
            "author": info.get("author"),
            "maintainer": info.get("maintainer"),
            "codeRepository": repo_url,
            "keywords": info.get("keywords", "").split(",") if info.get("keywords") else [],
            "programmingLanguage": "Python"
        }
    except Exception as e:
        print(f"⚠️ PyPI API failed for {package_name}: {e}")
        return {}


def extract_pip_show_metadata(package_name, tmp_path):
    """
    Extract metadata using pip show piped to codemetapy.
    Returns dict with metadata or empty dict on failure.
    """
    try:
        pip = shutil.which("pip") or "pip"
        
        # Run pip show and pipe to codemetapy
        with subprocess.Popen([pip, "show", package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p1:
            with subprocess.Popen(
                ["codemetapy", "-i", "pip", "-", "-O", tmp_path],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ) as p2:
                p1.stdout.close()
                stdout, stderr = p2.communicate()
                
                if p2.returncode == 0 and os.path.exists(tmp_path):
                    with open(tmp_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    print(f"⚠️ codemetapy pip processing failed: {stderr.decode()}")
                    return {}
                    
    except Exception as e:
        print(f"⚠️ pip show fallback failed: {e}")
        return {}


def extract_codemeta_from_source(package_dir, tmp_path):
    """
    Run codemetapy on source directory containing setup.py or pyproject.toml.
    Returns dict with metadata or empty dict on failure.
    """
    try:
        cmd = ["codemetapy", "-O", tmp_path]
        result = subprocess.run(
            cmd, 
            cwd=package_dir, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        if os.path.exists(tmp_path):
            with open(tmp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("⚠️ codemetapy succeeded but no output file created")
            return {}
            
    except subprocess.CalledProcessError as e:
        print(f"⚠️ codemetapy failed on source: {e.stderr}")
        return {}
    except Exception as e:
        print(f"⚠️ codemetapy source extraction failed: {e}")
        return {}


def extract_codemeta_from_installed(package_name, tmp_path):
    """
    Run codemetapy on installed package name.
    Returns dict with metadata or empty dict on failure.
    """
    try:
        cmd = ["codemetapy", package_name, "-O", tmp_path]
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        if os.path.exists(tmp_path):
            with open(tmp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("⚠️ codemetapy succeeded but no output file created")
            return {}
            
    except subprocess.CalledProcessError as e:
        print(f"⚠️ codemetapy failed on installed package: {e.stderr}")
        return {}
    except Exception as e:
        print(f"⚠️ codemetapy installed package extraction failed: {e}")
        return {}


def create_minimal_metadata(package_name):
    """
    Create minimal valid JSON-LD metadata as final fallback.
    """
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": package_name,
        "programmingLanguage": "Python"
    }


def extract_codemeta(package_dir, package_name=None):
    """
    Extract metadata using multiple fallback strategies:
    1. Detect setup.py/pyproject.toml and run codemetapy on source
    2. Try codemetapy on installed package name
    3. Fallback to PyPI JSON API
    4. Fallback to pip show piped to codemetapy
    5. Return minimal valid metadata stub
    
    Args:
        package_dir: Path to package source directory
        package_name: Package name (optional, inferred from dir if not provided)
    
    Returns:
        dict: Valid JSON-LD metadata with @context and @type at minimum
    """
    # Infer package name from directory if not provided
    if package_name is None:
        package_name = os.path.basename(os.path.abspath(package_dir))
    
    # Create temp file for codemetapy output
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    os.close(tmp_fd)  # Close file descriptor, keep path for later use
    
    try:
        # Strategy 1: Check for project files and run codemetapy on source
        project_files = ["setup.py", "pyproject.toml", "setup.cfg"]
        has_project_files = any(
            os.path.exists(os.path.join(package_dir, fn)) for fn in project_files
        )
        
        if has_project_files:
            print(f"📋 Found project files in {package_dir}, running codemetapy on source...")
            metadata = extract_codemeta_from_source(package_dir, tmp_path)
            if metadata:
                return metadata
        
        # Strategy 2: Try codemetapy on installed package
        print(f"📋 Trying codemetapy on installed package '{package_name}'...")
        metadata = extract_codemeta_from_installed(package_name, tmp_path)
        if metadata:
            return metadata
        
        # Strategy 3: Fallback to PyPI JSON API
        print(f"📋 Falling back to PyPI JSON API for '{package_name}'...")
        metadata = extract_pypi_metadata(package_name)
        if metadata:
            return metadata
        
        # Strategy 4: Fallback to pip show
        print(f"📋 Falling back to pip show for '{package_name}'...")
        metadata = extract_pip_show_metadata(package_name, tmp_path)
        if metadata:
            return metadata
        
        # Strategy 5: Final fallback - minimal metadata
        print(f"❌ All metadata extraction methods failed, returning minimal metadata for '{package_name}'")
        return create_minimal_metadata(package_name)
        
    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass  # Ignore cleanup errors