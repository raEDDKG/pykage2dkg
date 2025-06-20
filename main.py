import argparse, os, json
from datetime import datetime
from extractor.codemeta_wrapper import extract_codemeta
from extractor.hierarchical_walker import walk_python_modules_enhanced
from extractor.converter import convert_to_enhanced_jsonld
from extractor.runtime_extractor import extract_runtime_behavior

OUTPUT_DIR = 'output_jsonld'

def save_jsonld(data, name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.jsonld")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON-LD written to {path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Enhanced py2jsonld with advanced analysis')
    parser.add_argument('package_dir', help='Path to unpacked Python package')
    parser.add_argument('--name', required=True, help='Package name')
    args = parser.parse_args()

    print('📦 extracting codemeta metadata...')
    meta = extract_codemeta(args.package_dir, args.name)

    print('📁 extracting enhanced hierarchy + analysis...')
    modules = walk_python_modules_enhanced(args.package_dir)

    print("⏳ Running dynamic tests with noWorkflow/inspect…")
    runtime = extract_runtime_behavior(args.package_dir)

    print('🧠 converting to enhanced JSON-LD...')
    jsonld = convert_to_enhanced_jsonld(meta, modules, args.name, runtime, args.package_dir)

    ts = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    save_jsonld(jsonld, f"{args.name}_{ts}")