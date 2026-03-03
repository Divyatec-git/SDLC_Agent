import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

from db.models.final_output import create_final_output
from db.models.requirement_session import get_session
from db.models.user_story import create_user_stories

class RepoInfo(BaseModel):
    name: str = Field(description="A slug-style repository name (e.g., 'myapp-backend').")
    description: str = Field(description="A brief description of the repository.")

def github_agent(state, config):
    extracted_requirements = state["extracted_requirements"]
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        return {"email_status": "GitHub Token Missing - Repo not created"}

    # Use LLM to generate a name and description
    structured_llm = llm.with_structured_output(RepoInfo)
    prompt = ChatPromptTemplate.from_template("""
    Based on the following requirements, suggest a repository name (kebab-case) and a brief description.
    
    Requirements:
    {requirements}
    """)
    
    repo_info = structured_llm.invoke(prompt.format(requirements=extracted_requirements))
    repo_name = repo_info.name
    description = repo_info.description

    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": True
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        repo_url = response.json()["html_url"]
        repo_full_name = response.json()["full_name"]
        
        # Create README.md with Flowchart
        readme_url = f"https://api.github.com/repos/{repo_full_name}/contents/README.md"
        mermaid_diagram = state.get("mermaid_diagram", "")
        flowchart_image_url = state.get("flowchart_image_url", "")
        
        readme_content = f"""# {repo_name}

{description}

## Requirements Flowchart
![Flowchart]({flowchart_image_url})

```mermaid
{mermaid_diagram}
```

## Detailed Requirements
{extracted_requirements}
"""
        readme_payload = {
            "message": "Initialize README with requirements and flowchart",
            "content": base64.b64encode(readme_content.encode("utf-8")).decode("utf-8")
        }
        requests.put(readme_url, headers=headers, json=readme_payload)

        sessionId = get_session(thread_id)
        if sessionId:
            # Persist to MongoDB
            create_final_output(
                requirement_session_id=sessionId,
                flowchart_image_url=flowchart_image_url,
                repo_url=repo_url
                
        )

            if state["user_stories"]:
                create_user_stories(
                    requirement_session_id=sessionId,
                    stories=state["user_stories"]
                )

        return {
            "repo_url": repo_url,
            "email_status": f"GitHub Repo Created with Flowchart: {repo_url}"
        }
    elif response.status_code == 422:
        return {
            "email_status": "Repository name already exists. Try another name."
        }
    else:
        # If repo exists, try a variant or just return error
        return {
            "email_status": f"Failed to create GitHub Repo: {response.text}"
        }
