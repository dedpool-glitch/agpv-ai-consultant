from llm.client import call_llm
from constants import LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT

def explain_output(pvmaps_output, api_key):
    messages=[{"role":"system","content":LLM_SYSTEM_OUTPUT_EXPLANATION_PROMPT},
              {"role":"user","content":f"PVMAPS output:\n{pvmaps_output}"}]

    llm_explanation=call_llm(messages,api_key)
    return llm_explanation.strip()