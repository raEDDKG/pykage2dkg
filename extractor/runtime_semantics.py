"""
Runtime Semantics Module

Provides semantic analysis of runtime behavior using CodeBERT to generate
natural language summaries and embeddings for AI agent comprehension.
"""

from .codebert_summarizer import summarize_code
from .codebert_embedder import embed_code
from typing import Dict, Any, List


def generate_runtime_behavior_text(runtime_summary: Dict[str, Any]) -> str:
    """
    Generate descriptive text about runtime behavior for semantic analysis.
    """
    functions_executed = runtime_summary.get('functionsExecuted', 0)
    classes_instantiated = runtime_summary.get('classesInstantiated', 0)
    functions_skipped = runtime_summary.get('functionsSkipped', 0)
    classes_skipped = runtime_summary.get('classesSkipped', 0)
    execution_errors = runtime_summary.get('executionErrors', 0)
    has_runtime_data = runtime_summary.get('hasRuntimeData', False)
    
    if not has_runtime_data:
        return "No runtime analysis performed for this module. Runtime behavior unknown."
    
    # Build descriptive text
    parts = []
    
    # Success indicators
    if functions_executed > 0:
        parts.append(f"{functions_executed} function{'s' if functions_executed != 1 else ''} execute{'s' if functions_executed == 1 else ''} successfully without arguments")
    
    if classes_instantiated > 0:
        parts.append(f"{classes_instantiated} class{'es' if classes_instantiated != 1 else ''} can be instantiated without arguments")
    
    # Limitation indicators
    if functions_skipped > 0:
        parts.append(f"{functions_skipped} function{'s' if functions_skipped != 1 else ''} require{'s' if functions_skipped == 1 else ''} arguments and cannot be called directly")
    
    if classes_skipped > 0:
        parts.append(f"{classes_skipped} class{'es' if classes_skipped != 1 else ''} require{'s' if classes_skipped == 1 else ''} constructor arguments")
    
    # Error indicators
    if execution_errors > 0:
        parts.append(f"{execution_errors} execution error{'s' if execution_errors != 1 else ''} encountered during testing")
    
    # Determine overall safety assessment
    total_items = functions_executed + classes_instantiated + functions_skipped + classes_skipped
    safe_items = functions_executed + classes_instantiated
    
    if total_items == 0:
        safety_assessment = "Module contains no testable functions or classes"
    elif safe_items == 0:
        safety_assessment = "Module requires careful parameter handling - no items can be used without arguments"
    elif safe_items == total_items and execution_errors == 0:
        safety_assessment = "Module is safe for direct exploration - all items work without arguments"
    elif safe_items > total_items / 2:
        safety_assessment = "Module is mostly safe for exploration with some parameter requirements"
    else:
        safety_assessment = "Module requires careful parameter handling - most items need arguments"
    
    # Combine into coherent description
    if parts:
        behavior_description = ". ".join(parts) + "."
    else:
        behavior_description = "No executable items found in module."
    
    return f"Runtime Analysis: {behavior_description} {safety_assessment}"


def analyze_runtime_semantics(runtime_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate semantic analysis of runtime behavior including natural language summary
    and embedding vector for AI agent comprehension.
    
    Args:
        runtime_summary: The runtime summary data from runtime analysis
        
    Returns:
        Dictionary containing semantic summary and embedding
    """
    # Generate descriptive text about the runtime behavior
    behavior_text = generate_runtime_behavior_text(runtime_summary)
    
    # Generate semantic summary using CodeBERT
    semantic_summary = summarize_code(behavior_text)
    
    # Generate behavior embedding using CodeBERT
    behavior_embedding = embed_code(behavior_text)
    
    return {
        '@type': 'RuntimeSemantics',
        'behaviorDescription': behavior_text,
        'semanticSummary': semantic_summary,
        'behaviorEmbedding': behavior_embedding,
        'analysisMetadata': {
            'approach': 'codebert_semantic_analysis',
            'embeddingDimensions': len(behavior_embedding) if isinstance(behavior_embedding, list) else 768,
            'summaryMethod': 'transformers_or_fallback'
        }
    }


def analyze_execution_semantics(execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate semantic analysis for individual execution results.
    
    Args:
        execution_data: Individual execution result data
        
    Returns:
        Dictionary containing semantic analysis of the execution
    """
    if not execution_data.get('results'):
        return {
            '@type': 'ExecutionSemantics',
            'semanticSummary': 'No execution results available',
            'behaviorEmbedding': embed_code('No execution results available')
        }
    
    results = execution_data['results']
    module_name = results.get('module', 'unknown')
    
    # Build execution description
    functions_tested = results.get('functions_tested', [])
    classes_tested = results.get('classes_tested', [])
    functions_skipped = results.get('functions_skipped', [])
    classes_skipped = results.get('classes_skipped', [])
    errors = results.get('errors', [])
    
    execution_parts = []
    
    if functions_tested:
        execution_parts.append(f"Successfully executed functions: {', '.join(functions_tested[:3])}")
        if len(functions_tested) > 3:
            execution_parts.append(f"and {len(functions_tested) - 3} more")
    
    if classes_tested:
        execution_parts.append(f"Successfully instantiated classes: {', '.join(classes_tested[:3])}")
        if len(classes_tested) > 3:
            execution_parts.append(f"and {len(classes_tested) - 3} more")
    
    if functions_skipped:
        execution_parts.append(f"Functions requiring arguments: {len(functions_skipped)} items")
    
    if classes_skipped:
        execution_parts.append(f"Classes requiring constructor arguments: {len(classes_skipped)} items")
    
    if errors:
        execution_parts.append(f"Execution errors: {len(errors)} encountered")
    
    execution_text = f"Module {module_name} execution: " + ". ".join(execution_parts) + "."
    
    return {
        '@type': 'ExecutionSemantics',
        'executionDescription': execution_text,
        'semanticSummary': summarize_code(execution_text),
        'behaviorEmbedding': embed_code(execution_text)
    }


def enhance_runtime_data_with_semantics(runtime_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance existing runtime data with semantic analysis.
    
    Args:
        runtime_data: The complete runtime behavior data structure
        
    Returns:
        Enhanced runtime data with semantic analysis added
    """
    if not runtime_data:
        return runtime_data
    
    enhanced_data = runtime_data.copy()
    
    # Add semantics to individual executions if they exist
    if 'executions' in enhanced_data:
        for execution in enhanced_data['executions']:
            execution['semantics'] = analyze_execution_semantics(execution)
    
    # Add semantics to smart analysis executions
    if 'smart_analysis' in enhanced_data and 'executions' in enhanced_data['smart_analysis']:
        for execution in enhanced_data['smart_analysis']['executions']:
            execution['semantics'] = analyze_execution_semantics(execution)
    
    # Add semantics to noworkflow analysis executions
    if 'noworkflow_analysis' in enhanced_data and 'executions' in enhanced_data['noworkflow_analysis']:
        for execution in enhanced_data['noworkflow_analysis']['executions']:
            execution['semantics'] = analyze_execution_semantics(execution)
    
    return enhanced_data