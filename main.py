import argparse, os, json
from extractor.codemeta_wrapper import extract_codemeta
from extractor.hierarchical_walker import walk_python_modules
from extractor.converter import convert_to_jsonld

OUTPUT_DIR = "output_jsonld"

def save_jsonld(data, name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.jsonld")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON-LD written to {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("py2jsonld + embeddings/summaries + deep parse")
    parser.add_argument("package_dir", help="Path to unpacked Python package")
    parser.add_argument("--name", required=True, help="Package name")
    args = parser.parse_args()

    print("📦 extracting codemeta metadata...")
    meta = extract_codemeta(args.package_dir)

    print("📁 extracting hierarchy + summaries + embeddings...")
    modules = walk_python_modules(args.package_dir)

    print("🧠 converting to JSON-LD...")
    jsonld = convert_to_jsonld(meta, modules, args.name)

    save_jsonld(jsonld, args.name)