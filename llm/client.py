import requests

def call_llm(messages,api_key,model="llama4:latest"):
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

    response=requests.post(url,headers=headers,json=body)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


"""messages=[
    {"role":"user","content":"Please tell me a bit about yourself"}
]
response=call_llm(messages,api_key)
print(response)"""
