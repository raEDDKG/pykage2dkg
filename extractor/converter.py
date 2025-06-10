from datetime import datetime

def extract_analysis_summary(modules):
    tools_used = set()
    security_issues = 0
    type_errors = 0
    cross_lang = False
    for module in modules:
        for cf in module.get('hasPart', []):
            enh = cf.get('enhanced')
            if enh:
                if enh.get('libcst'): tools_used.add('libcst')
                if enh.get('parso'): tools_used.add('parso')
                if enh.get('typeAnalysis'): 
                    tools_used.add('type-analysis')
                    type_errors += enh['typeAnalysis'].get('summary', {}).get('totalErrors', 0)
                if enh.get('securityAnalysis'):
                    tools_used.add('security-analysis')
                    security_issues += enh['securityAnalysis'].get('summary', {}).get('totalVulnerabilities', 0)
            if cf.get('crossLanguage'):
                cross_lang = True
                tools_used.add('tree-sitter')
    return {
        'toolsUsed': list(tools_used),
        'security': {'totalIssues': security_issues, 'riskLevel': 'HIGH' if security_issues>10 else 'MEDIUM' if security_issues>0 else 'LOW'},
        'types': {'totalErrors': type_errors, 'coverage': 'PARTIAL' if type_errors>0 else 'GOOD'},
        'crossLanguageSupport': cross_lang
    }

def convert_to_enhanced_jsonld(metadata, modules, package_name):
    metadata.setdefault('@context', [
        'https://schema.org',
        {'analysis': 'https://pykage2dkg.org/analysis#', 'security': 'https://pykage2dkg.org/security#', 'types': 'https://pykage2dkg.org/types#'}
    ])
    metadata['@type'] = 'SoftwareSourceCode'
    metadata['name'] = package_name
    metadata['programmingLanguage'] = 'Python'
    metadata['hasPart'] = modules
    summary = extract_analysis_summary(modules)
    metadata['analysisMetadata'] = {
        '@type': 'AnalysisMetadata',
        'timestamp': datetime.utcnow().isoformat(),
        'toolsUsed': summary['toolsUsed'],
        'securitySummary': summary['security'],
        'typeSummary': summary['types'],
        'crossLanguageSupport': summary['crossLanguageSupport']
    }
    return metadata
