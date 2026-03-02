# agents/code_completion_notification_agent.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def code_completion_notification_agent(state):
    stakeholder_emails = state["stakeholder_emails"]
    smtp_config = state["smtp_config"]
    repo_url = state.get("repo_url", "")
    tech_stack = state.get("selected_tech_stack", "Selected Tech Stack")
    
    email_body = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
        <h2 style="color: #27ae60;">Code Generation Complete!</h2>
        <p>The core boilerplate for your project has been generated and pushed to your repository.</p>
        
        <p><b>Tech Stack:</b> {tech_stack}</p>
        <p><b>GitHub Repository:</b> <a href="{repo_url}" style="color: #3498db; text-decoration: none;">{repo_url}</a></p>
        
        <p>You can now clone the repository and start developing!</p>
        
        <p style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px;">Regards,<br><b>SDLC Agent Team</b></p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Project Code Generated Successfully"
        msg["From"] = smtp_config["sender"]
        msg["To"] = ", ".join(stakeholder_emails)

        part = MIMEText(email_body, "html")
        msg.attach(part)

        print(f"DEBUG: Sending completion notification to: {stakeholder_emails}")
        server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
        server.starttls()
        server.login(smtp_config["sender"], smtp_config["password"])
        server.sendmail(smtp_config["sender"], stakeholder_emails, msg.as_string())
        server.quit()

        status = "Code Completion Notification Sent"
    except Exception as e:
        status = f"Code Completion Notification Failed: {str(e)}"

    return {
        "email_status": status
    }
