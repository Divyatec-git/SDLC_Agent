# agents/code_generation_agent.py
import os
import requests
import base64
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def code_generation_agent(state):
    requirements = state["extracted_requirements"]
    tech_stack = state["selected_tech_stack"]
    repo_url = state["repo_url"]

    # Extract owner/repo from URL e.g. https://github.com/user/repo
    repo_name_full = repo_url.replace("https://github.com/", "")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    prompt = ChatPromptTemplate.from_template("""
    You are a senior software engineer.
    Based on the requirements and the selected tech stack, generate core boilerplate code for the project.

    Requirements:
    {requirements}

    Selected Tech Stack:
    {tech_stack}

    Generate files that form the foundation of this project.

    Format your response EXACTLY as a series of blocks like this:
    ---FILE: path/to/file1---
    [content of file1]
    ---FILE: path/to/file2---
    [content of file2]

    Rules:
    - Include at least: README.md, package.json or requirements.txt, and 2-3 core source files.
    - Keep file paths relative (no leading slash).
    - Focus on a well-structured, functional starting point.
    """)

    response = llm.invoke(prompt.format(requirements=requirements, tech_stack=tech_stack))
    content = response.content

    # Parse and push each file to GitHub
    files = content.split("---FILE: ")
    pushed = []
    for file_block in files:
        if not file_block.strip():
            continue
        try:
            parts = file_block.split("---", 1)
            file_path = parts[0].strip()
            file_content = parts[1].strip() if len(parts) > 1 else ""

            if not file_path or not file_content:
                continue

            url = f"https://api.github.com/repos/{repo_name_full}/contents/{file_path}"
            payload = {
                "message": f"Add {file_path}",
                "content": base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
            }
            resp = requests.put(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                pushed.append(file_path)
            else:
                print(f"Warning: Failed to push {file_path}: {resp.text}")
        except Exception as e:
            print(f"Error processing file block: {e}")

    pushed_list = ", ".join(pushed) if pushed else "none"
    return {
        "email_status": f"Code generated ({len(pushed)} files) and pushed to {repo_url}"
    }
