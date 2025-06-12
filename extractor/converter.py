from datetime import datetime
import os
from typing import Dict, List, Any, Optional
from .runtime_semantics import analyze_runtime_semantics, enhance_runtime_data_with_semantics
from .usage_mapper import enhance_with_usage_mapping
from .import_validator import enhance_with_import_validation

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

def distribute_runtime_behavior_to_files(modules: List[Dict[str, Any]], runtime_behavior: Dict[str, Any], package_path: str) -> None:
    """
    Distribute runtime behavior data to the appropriate CodeFile sections.
    This makes it easier for AI agents to understand the connection between static code and runtime behavior.
    """
    if not runtime_behavior:
        return
    
    # Extract execution data from both smart analysis and noworkflow analysis
    all_executions = []
    
    # Get smart analysis executions
    smart_analysis = runtime_behavior.get('smart_analysis', {})
    if smart_analysis.get('executions'):
        all_executions.extend(smart_analysis['executions'])
    
    # Get noworkflow analysis executions  
    noworkflow_analysis = runtime_behavior.get('noworkflow_analysis', {})
    if noworkflow_analysis.get('executions'):
        all_executions.extend(noworkflow_analysis['executions'])
    
    # If it's not a combined analysis, treat the whole thing as executions
    if not smart_analysis and not noworkflow_analysis and runtime_behavior.get('executions'):
        all_executions.extend(runtime_behavior['executions'])
    
    # Create a mapping from module names to runtime data
    module_runtime_map = {}
    
    for execution in all_executions:
        if execution.get('results') and execution['results'].get('module'):
            module_name = execution['results']['module']
            if module_name not in module_runtime_map:
                module_runtime_map[module_name] = {
                    '@type': 'RuntimeBehavior',
                    'executions': [],
                    'summary': {
                        'functions_tested': [],
                        'classes_tested': [],
                        'functions_skipped': [],
                        'classes_skipped': [],
                        'errors': []
                    }
                }
            
            module_runtime_map[module_name]['executions'].append(execution)
            
            # Aggregate summary data
            if execution.get('results'):
                results = execution['results']
                summary = module_runtime_map[module_name]['summary']
                summary['functions_tested'].extend(results.get('functions_tested', []))
                summary['classes_tested'].extend(results.get('classes_tested', []))
                summary['functions_skipped'].extend(results.get('functions_skipped', []))
                summary['classes_skipped'].extend(results.get('classes_skipped', []))
                summary['errors'].extend(results.get('errors', []))
    
    # Now distribute this data to the appropriate CodeFile sections
    for module in modules:
        for code_file in module.get('hasPart', []):
            if code_file.get('@type') == 'CodeFile':
                file_name = code_file.get('name', '')
                
                # Try to match this file with runtime data
                matching_runtime_data = None
                
                # Look for exact module name matches
                for module_name, runtime_data in module_runtime_map.items():
                    # Convert module name to file path (e.g., "emoji.core" -> "core.py")
                    if '.' in module_name:
                        module_file = module_name.split('.')[-1] + '.py'
                    else:
                        module_file = module_name + '.py'
                    
                    if file_name == module_file:
                        matching_runtime_data = runtime_data
                        break
                
                # If we found matching runtime data, add it to the CodeFile
                if matching_runtime_data:
                    # Enhance runtime data with semantic analysis
                    enhanced_runtime_data = enhance_runtime_data_with_semantics(matching_runtime_data)
                    code_file['runtimeBehavior'] = enhanced_runtime_data
                    
                    # Also add a summary for quick reference
                    summary = matching_runtime_data['summary']
                    runtime_summary = {
                        '@type': 'RuntimeSummary',
                        'functionsExecuted': len(set(summary['functions_tested'])),
                        'classesInstantiated': len(set(summary['classes_tested'])),
                        'functionsSkipped': len(set(summary['functions_skipped'])),
                        'classesSkipped': len(set(summary['classes_skipped'])),
                        'executionErrors': len(summary['errors']),
                        'hasRuntimeData': True
                    }
                    
                    # Add semantic analysis to the runtime summary
                    runtime_semantics = analyze_runtime_semantics(runtime_summary)
                    runtime_summary['semantics'] = runtime_semantics
                    
                    code_file['runtimeSummary'] = runtime_summary
                else:
                    # Add empty runtime summary to indicate no runtime data available
                    empty_runtime_summary = {
                        '@type': 'RuntimeSummary',
                        'hasRuntimeData': False,
                        'reason': 'No runtime analysis performed for this file',
                        'functionsExecuted': 0,
                        'classesInstantiated': 0,
                        'functionsSkipped': 0,
                        'classesSkipped': 0,
                        'executionErrors': 0
                    }
                    
                    # Add semantic analysis even for empty runtime data
                    runtime_semantics = analyze_runtime_semantics(empty_runtime_summary)
                    empty_runtime_summary['semantics'] = runtime_semantics
                    
                    code_file['runtimeSummary'] = empty_runtime_summary

def convert_to_enhanced_jsonld(metadata, modules, package_name, runtime_behavior=None, package_path=None):
    metadata.setdefault('@context', [
        'https://schema.org',
        {'analysis': 'https://pykage2dkg.org/analysis#', 'security': 'https://pykage2dkg.org/security#', 'types': 'https://pykage2dkg.org/types#', 'runtime': 'https://pykage2dkg.org/runtime#', 'semantics': 'https://pykage2dkg.org/semantics#'}
    ])
    metadata['@type'] = 'SoftwareSourceCode'
    metadata['name'] = package_name
    metadata['programmingLanguage'] = 'Python'
    metadata['hasPart'] = modules
    
    # Distribute runtime behavior to individual files
    if runtime_behavior and package_path:
        distribute_runtime_behavior_to_files(modules, runtime_behavior, package_path)
    
    summary = extract_analysis_summary(modules)
    metadata['analysisMetadata'] = {
        '@type': 'AnalysisMetadata',
        'timestamp': datetime.utcnow().isoformat(),
        'toolsUsed': summary['toolsUsed'],
        'securitySummary': summary['security'],
        'typeSummary': summary['types'],
        'crossLanguageSupport': summary['crossLanguageSupport']
    }
    
    # Add overall runtime summary if runtime behavior was provided
    if runtime_behavior:
        metadata['runtimeAnalysisMetadata'] = {
            '@type': 'RuntimeAnalysisMetadata',
            'tool': runtime_behavior.get('@type', 'Unknown'),
            'distributedToFiles': True,
            'analysisApproach': 'smart_introspection_with_noworkflow' if runtime_behavior.get('smart_analysis') and runtime_behavior.get('noworkflow_analysis') else 'smart_introspection_only',
            'semanticAnalysis': True,
            'semanticTool': 'codebert_runtime_semantics',
            'enhancedWithEmbeddings': True
        }
    
    # Add AI Agent guidance for DKG usage
    if package_path:
        metadata = enhance_with_usage_mapping(metadata, package_path, package_name)
        # Add real import validation
        metadata = enhance_with_import_validation(metadata, package_path, package_name)
    
    return metadata
