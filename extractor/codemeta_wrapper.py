# extractor/codemeta_wrapper.py

import subprocess
import json
import tempfile
import os
import shutil
import requests  # new
from urllib.parse import quote_plus

def extract_pypi_metadata(package_name):
    """
    Fetch metadata from PyPI JSON API.
    """
    url = f"https://pypi.org/pypi/{quote_plus(package_name)}/json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        info = resp.json()["info"]
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareSourceCode",
            "name": info.get("name", package_name),
            "version": info.get("version"),
            "description": info.get("summary"),
            "license": info.get("license"),
            "author": info.get("author"),
            "codeRepository": info.get("home_page") or info.get("project_urls", {}).get("Homepage"),
        }
    except Exception:
        return {}

def extract_codemeta(package_dir, package_name):
    """
    Attempt codemetapy first; if it errors, fallback to PyPI API, then pip show.
    """
    # temp file for codemetapy output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    # 1) If project files exist, run codemetapy in that dir
    if any(os.path.exists(os.path.join(package_dir, fn)) for fn in ("setup.py","pyproject.toml")):
        cmd = ["codemetapy", "-O", tmp_path]
        cwd = package_dir
    else:
        # 2) Try codemetapy on the package name (installed package)
        cmd = ["codemetapy", package_name, "-O", tmp_path]
        cwd = os.getcwd()

    try:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print("⚠️ codemetapy failed; falling back to PyPI JSON API…")
        meta = extract_pypi_metadata(package_name)
        if meta:
            return meta

        # Final fallback: pip show
        print("ℹ️ PyPI API failed; falling back to `pip show`…")
        try:
            pip = shutil.which("pip") or "pip"
            p1 = subprocess.Popen([pip, "show", package_name], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(
                ["codemetapy", "-i", "pip", "-", "-O", tmp_path],
                stdin=p1.stdout
            )
            p1.stdout.close()
            p2.wait()
            with open(tmp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            print("❌ pip-show fallback failed; returning minimal metadata.")
            return {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": package_name}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
