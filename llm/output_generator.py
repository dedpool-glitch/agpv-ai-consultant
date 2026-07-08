import json

from llm.client import call_llm
from llm.prompts import LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT

def explain_output(pvmaps_output, api_key, user_profile=None):
    messages=[{"role":"system","content":LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT},
              {"role":"user","content":f"PVMAPS output:\n{json.dumps(pvmaps_output, indent=2)}\nUser Profile:\n{json.dumps(user_profile, indent=2)}\nGenerate a clear, simple explanation of the PVMAPS output that can be easily understood by the user."}]

    llm_explanation=call_llm(messages,api_key)
    return llm_explanation.strip()
