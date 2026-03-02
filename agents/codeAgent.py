# import requests
# import json

# response = requests.post(
#   url="https://openrouter.ai/api/v1/chat/completions",
#   headers={
#     "Authorization": "Bearer sSasas",
#     "Content-Type": "application/json",
#   },
#   data=json.dumps({
#     "model": "openrouter/free",
#     "messages": [
#       {
#         "role": "user",
#         "content": "Hello! What can you help me with today?"
#       }
#     ]
#   })
# )

# data = response.json()
# print(data['choices'][0]['message']['content'])
# # Check which model was selected
# print('Model used:', data['model'])


import os
import base64
import requests
from urllib.parse import urlparse
from langchain_openai import ChatOpenAI

# ==============================
# CONFIG
# ==============================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# This comes from your DB
repo_url = "https://github.com/yourusername/auto-generated-landing-page"

# ==============================
# STEP 1: Generate Code
# ==============================

llm = ChatOpenAI(
    model="meta-llama/llama-3.3-70b-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

response = llm.invoke("Create a clean simple HTML landing page with inline CSS.")
html_code = response.content

print("✅ Code Generated")

# ==============================
# STEP 2: Extract owner/repo
# ==============================

def extract_repo_full_name(repo_url):
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")
    return f"{path_parts[0]}/{path_parts[1]}"

repo_full_name = extract_repo_full_name(repo_url)

# ==============================
# STEP 3: Upload index.html
# ==============================

upload_url = f"https://api.github.com/repos/{repo_full_name}/contents/index.html"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

encoded_content = base64.b64encode(html_code.encode("utf-8")).decode("utf-8")

payload = {
    "message": "Add auto-generated landing page",
    "content": encoded_content
}

response = requests.put(upload_url, headers=headers, json=payload)

if response.status_code in [200, 201]:
    print("🚀 index.html uploaded successfully!")
    print("Repo:", repo_url)
else:
    print("❌ Upload failed:", response.text)