def convert_to_jsonld(metadata, modules, package_name):
    metadata.setdefault("@context", "https://schema.org")
    metadata["@type"] = "SoftwareSourceCode"
    metadata["name"] = package_name
    metadata["programmingLanguage"] = "Python"
    metadata["hasPart"] = modules
    return metadata