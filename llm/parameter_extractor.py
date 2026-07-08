import json
from llm.client import call_llm
from llm.prompts import LLM_SYSTEM_EXTRACTION_PROMPT

def extract_questionnaire_parameter(field,question,user_response,api_key):
    messages=[
        {"role":"system","content":LLM_SYSTEM_EXTRACTION_PROMPT},
        {"role":"user","content":f"Field: {field}\nQuestion: {question}\nUser Response: {user_response}\nExtract the value for the field in valid JSON format."}
    ]

    llm_response=call_llm(messages,api_key)

    try:
        extracted_json=json.loads(llm_response)
    except json.JSONDecodeError:
        extracted_json=None

    return extracted_json

