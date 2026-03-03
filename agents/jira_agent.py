from jira import JIRA
import os
from dotenv import load_dotenv
from db.models.final_output import update_final_output
from db.models.requirement_session import get_session
load_dotenv()


def get_jira_client():
    return JIRA(
        server=os.getenv("JIRA_URL"),
        basic_auth=(
            os.getenv("JIRA_EMAIL"),
            os.getenv("JIRA_API_TOKEN"),
        ),
    )


def ensure_project_exists(jira, project_key, project_name):
    """
    Create project only if it does not already exist.
    """
    try:
        jira.project(project_key)
        print("Project already exists:", project_key)
    except Exception:
        print("Creating project:", project_key)
        jira.create_project(
            key=project_key,
            name=project_name,
            projectTypeKey="software",
            projectTemplateKey="com.pyxis.greenhopper.jira:gh-scrum-template",
            lead=os.getenv("JIRA_EMAIL"),
            description="Auto-created by SDLC Agent",
        )


def get_valid_issue_type_id(jira, project_key):
    """
    Fetch allowed issue types dynamically (safe for team/company managed).
    """
    meta = jira.createmeta(
        projectKeys=project_key,
        expand="projects.issuetypes.fields"
    )

    if not meta["projects"]:
        raise Exception("No create permission for this project")

    issuetypes = meta["projects"][0]["issuetypes"]

    # Prefer Story if available
    for itype in issuetypes:
        if itype["name"].lower() in ["story", "user story"]:
            return itype["id"]

    # Otherwise return first available
    return issuetypes[0]["id"]


def jira_agent(state, config):
    """
    LangGraph node that pushes generated user stories to Jira.
    """

    jira = get_jira_client()

    project_key = os.getenv("JIRA_PROJECT_KEY")
    project_name = os.getenv("JIRA_PROJECT_NAME")

    ensure_project_exists(jira, project_key, project_name)

    issue_type_id = get_valid_issue_type_id(jira, project_key)

    stories = state["user_stories"]

    created_issues = []

    for story in stories:

        # Base description
        full_description = story["description"]

        # Merge acceptance criteria if exists
        if story.get("acceptance_criteria"):
            acceptance_text = "\n\n\nAcceptance Criteria:\n- " + "\n- ".join(
                story["acceptance_criteria"]
            )
            full_description += acceptance_text

        issue_dict = {
            "project": {"key": project_key},
            "summary": story["title"],
            "description": full_description,
            "issuetype": {"id": issue_type_id},
        }

        new_issue = jira.create_issue(fields=issue_dict)

        created_issues.append(new_issue.key)

    thread_id = config.get("configurable", {}).get("thread_id", "default")
    sessionId = get_session(thread_id)
    if sessionId:
        # Update DB once after all issues created
        update_final_output(
            sessionId,
            created_issues,
            os.getenv("JIRA_URL"),
            True
        )

    return {
        "jira_issue_keys": created_issues,
        "jira_url": os.getenv("JIRA_URL"),
        "jira_status": True
    }