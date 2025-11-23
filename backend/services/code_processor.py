from typing import Dict, Any
import os
import re
from fastapi import HTTPException

def generate_documentation(code: str) -> Dict[str, str]:
    """Generate documentation and summary using local open-source models."""
    
    # Try to use local T5/FLAN-T5 if available
    try:
        return generate_documentation_with_local_model(code)
    except Exception:
        # Fallback to rule-based if models fail
        return generate_documentation_rule_based(code)

def generate_documentation_rule_based(code: str) -> Dict[str, str]:
    """Generate documentation and summary using simple rule-based approach (no API required)."""
    
    # Simple rule-based documentation generation
    documentation_lines = []
    summary_parts = []
    
    # Extract function definitions
    functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
    classes = re.findall(r'class\s+(\w+)[\(\:]', code)
    
    if functions:
        documentation_lines.append("Functions:")
        for func in functions:
            documentation_lines.append(f"  - {func}(): Function defined")
            summary_parts.append(f"function {func}")
    
    if classes:
        documentation_lines.append("\nClasses:")
        for cls in classes:
            documentation_lines.append(f"  - {cls}: Class defined")
            summary_parts.append(f"class {cls}")
    
    # Look for common patterns
    if "print(" in code:
        documentation_lines.append("\n- Contains print statements")
        summary_parts.append("output operations")
    
    if "import " in code or "from " in code:
        documentation_lines.append("\n- Imports external modules")
        summary_parts.append("module imports")
    
    if "if __name__" in code:
        documentation_lines.append("\n- Contains main execution block")
        summary_parts.append("main execution")
    
    # Generate documentation
    if not documentation_lines:
        documentation = "Code analysis complete. No specific functions or classes detected."
    else:
        documentation = "\n".join(documentation_lines)
    
    # Generate summary
    if summary_parts:
        summary = f"This code contains {', '.join(summary_parts)}."
    else:
        summary = "This is a Python code snippet."
    
    return {
        "documentation": documentation,
        "summary": summary
    }

def generate_documentation_with_local_model(code: str) -> Dict[str, str]:
    """Generate documentation using local open-source models (T5/FLAN-T5)."""
    try:
        from transformers import T5ForConditionalGeneration, T5Tokenizer, FlanT5ForConditionalGeneration
        import torch
        
        # Try FLAN-T5 first (better for instructions), then T5
        models_to_try = [
            ("google/flan-t5-small", FlanT5ForConditionalGeneration, "FLAN-T5 Small"),
            ("t5-small", T5ForConditionalGeneration, "T5 Small"),
            ("google/flan-t5-base", FlanT5ForConditionalGeneration, "FLAN-T5 Base"),
        ]
        
        for model_name, model_class, display_name in models_to_try:
            try:
                print(f"Trying {display_name}...")
                tokenizer = T5Tokenizer.from_pretrained(model_name)
                model = model_class.from_pretrained(model_name)
                
                # Prepare prompt for documentation generation
                prompt = f"Generate documentation and summary for this Python code:\n\n{code}\n\nDocumentation:"
                
                inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
                
                with torch.no_grad():
                    outputs = model.generate(
                        inputs.input_ids,
                        max_length=200,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Clean up the generated text
                if "Documentation:" in generated_text:
                    generated_text = generated_text.split("Documentation:", 1)[1].strip()
                
                # Split into documentation and summary
                lines = generated_text.split('\n')
                documentation = '\n'.join(lines).strip()
                summary = lines[0] if lines else generated_text[:100] + "..."
                
                if len(summary) > 150:
                    summary = summary[:147] + "..."
                
                return {
                    "documentation": documentation or "Documentation generated successfully.",
                    "summary": summary or "Code documentation summary."
                }
                
            except Exception as e:
                print(f"Failed to load {display_name}: {e}")
                continue
        
        # If all models fail, fallback to rule-based
        print("All models failed, using rule-based approach")
        return generate_documentation_rule_based(code)
        
    except ImportError:
        # transformers not available, fallback to rule-based
        print("transformers not installed, using rule-based approach")
        return generate_documentation_rule_based(code)
    except Exception as e:
        print(f"Error with local models: {e}, using rule-based approach")
        return generate_documentation_rule_based(code)