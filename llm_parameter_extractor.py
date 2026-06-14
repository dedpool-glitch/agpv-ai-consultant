import json
from llm_client import call_llm
from constants import LLM_SYSTEM_PROMPT

def extract_questionnaire_parameter(field,question,user_response,api_key):
    messages=[
        {"role":"system","content":LLM_SYSTEM_PROMPT},
        {"role":"user","content":f"Field: {field}\nQuestion: {question}\nUser Response: {user_response}\nExtract the value for the field in valid JSON format."}
    ]

    llm_response=call_llm(messages,api_key)

    try:
        extracted_value=json.loads(llm_response)
    except json.JSONDecodeError:
        extracted_value=None

    return extracted_value