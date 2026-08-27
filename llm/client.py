import requests

def call_llm(messages,api_key,model="llama4:latest",temperature=None):
    url="https://genai.rcac.purdue.edu/api/chat/completions"

    headers={
        "Authorization":f"Bearer {api_key}",
        "Content-Type":"application/json"
    }

    body={
        "model":model,
        "messages":messages,
        "stream":False
    }
    if temperature is not None:
        body["temperature"] = temperature

    response=requests.post(url,headers=headers,json=body,timeout=30)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]

