from jira import JIRA
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "").strip()


def main():
    try:
        print("Connecting to Jira...")

        jira = JIRA(
            server=JIRA_URL,
            basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        )

        print("✅ Connected successfully!")
        print("Authenticated as:", jira.current_user())

        # 🔥 Fetch allowed issue types for this project
        print("\nFetching allowed issue types for project:", JIRA_PROJECT_KEY)

        meta = jira.createmeta(
            projectKeys=JIRA_PROJECT_KEY,
            expand="projects.issuetypes.fields"
        )

        if not meta["projects"]:
            raise Exception("No create permission or invalid project key.")

        allowed_issue_types = meta["projects"][0]["issuetypes"]

        print("\nAllowed Issue Types:")
        for itype in allowed_issue_types:
            print("•", itype["name"], "| ID:", itype["id"])

        # 👉 Automatically pick the first allowed issue type
        selected_issue_type = allowed_issue_types[0]

        print("\nUsing Issue Type:", selected_issue_type["name"])

        print("\nCreating test issue...")

        issue_dict = {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": "Test Issue from Python Script",
            "description": "Created via Jira API",
            "issuetype": {"id": selected_issue_type["id"]},
        }

        new_issue = jira.create_issue(fields=issue_dict)

        print("\n✅ Task created successfully!")
        print("Issue Key:", new_issue.key)
        print("Open it here:")
        print(f"{JIRA_URL}/browse/{new_issue.key}")

    except Exception as e:
        print("\n❌ ERROR OCCURRED:")
        print(e)


if __name__ == "__main__":
    main()