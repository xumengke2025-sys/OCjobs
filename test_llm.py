
import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env
project_root_env = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(project_root_env)

api_key = os.environ.get('LLM_API_KEY')
base_url = os.environ.get('LLM_BASE_URL')
model = os.environ.get('LLM_MODEL_NAME')

print(f"Testing LLM with:")
print(f"Base URL: {base_url}")
print(f"Model: {model}")

client = OpenAI(api_key=api_key, base_url=base_url)

try:
    print("\nAttempting chat completion without json_object...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=10
    )
    print(f"Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Failed without json_object: {str(e)}")

try:
    print("\nAttempting chat completion WITH response_format={'type': 'json_object'}...")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
            {"role": "user", "content": "Return a JSON with a 'status' field set to 'ok'."}
        ],
        response_format={"type": "json_object"},
        max_tokens=50
    )
    print(f"Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"Failed WITH json_object: {str(e)}")
