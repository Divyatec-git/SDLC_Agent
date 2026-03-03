import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db.models.requirement_session import update_session,get_session
from db.models.user_story import create_user_stories

def final_notification_agent(state, config):
    stakeholder_emails = state["stakeholder_emails"]
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    smtp_config = state["smtp_config"]
    repo_url = state.get("repo_url", "")
    flowchart_image_url = state.get("flowchart_image_url", "")
    extracted_requirements = state.get("extracted_requirements", "")

    repo_name = repo_url.split('/')[-1] if repo_url and '/' in repo_url else "Project"

    email_body = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #2c3e50;">Project Initialized: {repo_name}</h2>
        <p>We are pleased to inform you that the requirements have been clarified and the project has been successfully initialized.</p>

        <p><b>GitHub Repository:</b> {f'<a href="{repo_url}" style="color: #3498db; text-decoration: none;">{repo_url}</a>' if repo_url else '<span style="color: #e74c3c;">Not created</span>'}</p>

        <h3 style="border-bottom: 2px solid #eee; padding-bottom: 5px;">Requirement Flowchart</h3>
        <div style="margin: 20px 0;">
            <img src="{flowchart_image_url}" alt="Flowchart Diagram" style="max-width: 100%; border: 1px solid #ddd; border-radius: 8px; background-color: white; padding: 10px;">
        </div>
        <p><a href="{flowchart_image_url}" style="font-size: 0.9em; color: #7f8c8d;">View Full Size Diagram</a></p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

        <h3 style="border-bottom: 2px solid #eee; padding-bottom: 5px;">Final Clarified Requirements</h3>
        <pre style="white-space: pre-wrap; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; font-size: 14px;">
{extracted_requirements}
        </pre>

        <p style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">Regards,<br><b>SDLC Agent Team</b></p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Project Initialized: {repo_name} — Action Required"
        msg["From"] = smtp_config["sender"]
        msg["To"] = ", ".join(stakeholder_emails)

        part = MIMEText(email_body, "html")
        msg.attach(part)

        server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
        server.starttls()
        server.login(smtp_config["sender"], smtp_config["password"])
        server.sendmail(smtp_config["sender"], stakeholder_emails, msg.as_string())
        server.quit()

        status = "Final Notification Sent"
    except Exception as e:
        status = f"Final Notification Failed: {str(e)}"

    # Update MongoDB session status
    update_session(
        session_id=thread_id,
        email_event={
            "round": 1,  # 0 or special marker for final notification
            "status": status
        }
    )

    sessionId = get_session(thread_id)
    if sessionId:
        if state["user_stories"]:
            create_user_stories(
                requirement_session_id=sessionId,
                stories=state["user_stories"]
            )

    return {
        "email_status": status
    }
