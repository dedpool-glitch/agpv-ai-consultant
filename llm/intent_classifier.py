from constants import LLM_SYSTEM_INTENT_CLASSIFIER_PROMPT
from llm.client import call_llm
def classify_intent(field,question,user_response,api_key):
    messages = [
        {"role": "system", "content": LLM_SYSTEM_INTENT_CLASSIFIER_PROMPT},
        {
        "role": "user",
        "content": f"""
        Field: {field}
        Question: {question}
        User response: {user_response}

        Classify the user's intent.
        """
        }
    ]

    response = call_llm(messages, api_key)
    return response.strip()
    