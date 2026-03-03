# state.py

from typing import TypedDict, List

class SMTPConfig(TypedDict):
    server: str
    port: int
    sender: str
    password: str

class SDLCState(TypedDict):
    raw_document: str
    extracted_requirements: str
    clarification_questions: List[str]
    
    stakeholder_emails: List[str]
    email_status: str
    smtp_config: SMTPConfig
    stakeholder_response: str
    is_clarified: bool
    repo_url: str
    mermaid_diagram: str
    flowchart_image_url: str
    thread_id: str
    user_stories: dict
    jira_issue_keys: list
    jira_url: str
    jira_status: bool
    
