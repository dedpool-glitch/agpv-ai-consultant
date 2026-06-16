from constants import LLM_SYSTEM_QUESTION_GENERATOR_PROMPT
from llm.client import call_llm
def generate_question(field, state, api_key):
    messages=[
        {"role":"system","content":LLM_SYSTEM_QUESTION_GENERATOR_PROMPT},
        {"role":"user","content":f"Field: {field}\nCurrent State: {state}\nGenerate a clear, simple question to ask the user to collect the value for the field."}
    ]

    llm_generated_question=call_llm(messages,api_key)
    return llm_generated_question.strip()