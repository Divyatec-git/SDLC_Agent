# agents/code_generation_agent.py
import os
import requests
import base64
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from urllib.parse import urlparse
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def code_generation_agent(requirements, tech_stack, repo_url):
    

    # Extract owner/repo from URL e.g. https://github.com/user/repo
    # repo_name_full1 = repo_url.replace("https://github.com/", "")
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return {"email_status": f"Error: Invalid GitHub repository URL provided: {repo_url}"}
    repo_name_full = f"{parts[0]}/{parts[1]}"

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    prompt = ChatPromptTemplate.from_template("""
    You are an expert full-stack software architect and UI/UX designer.
    Your goal is to generate a professional, production-ready, and visually stunning project foundation based on the requirements and tech stack.

    Requirements:
    {requirements}

    Selected Tech Stack:
    {tech_stack}

    ### Design Guidelines:
    - **Aesthetics**: Use a modern, premium design. Incorporate vibrant but harmonious color palettes, subtle gradients, and glassmorphism where appropriate.
    - **UX**: Ensure the interface is intuitive, responsive, and feels 'alive' with micro-animations and hover effects.
    - **Typography**: Use modern, clean fonts (e.g., Inter, Roboto).
    - **Professionalism**: The code must be well-organized, commented, and follow best practices for the chosen tech stack.

    ### Project Requirements:
    - Generate a complete set of files to make the project functional and ready for further development.
    - Include:
        - A comprehensive README.md with setup instructions and project overview.
        - Dependency management files (e.g., package.json, requirements.txt, go.mod).
        - Configuration files (e.g., .gitignore, tailwind.config.js if applicable).
        - A well-structured source directory (e.g., src/, components/, styles/).
        - At least one polished, fully functional landing page or dashboard reflecting the requirements.

    ### Output Format:
    Format your response EXACTLY as a series of blocks like this:
    ---FILE: path/to/file1---
    [content of file1]
    ---FILE: path/to/file2---
    [content of file2]

    Rules:
    - Keep file paths relative (no leading slash).
    - No conversational text, only the file blocks.
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
