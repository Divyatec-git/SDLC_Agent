import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from db.models.requirement_session import update_session, get_session , create_session
from db.models.requirement_version import create_version
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def clarification_agent(state, config):
    extracted_requirements = state["extracted_requirements"]
    clarification_questions = state["clarification_questions"]
    stakeholder_emails = state["stakeholder_emails"]
    smtp_config = state["smtp_config"]
    
    # Get thread_id from config
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    # Step 1: Format structured email using LLM
    prompt = ChatPromptTemplate.from_template("""
    You are a senior business analyst.

    We have some requirements extracted from a document, and we might have received some initial clarifications.
    We need further details to proceed with the development.

    Requirements & Context so far:
    {requirements}

    Remaining Clarification Questions:
    {questions}

    Task:
    Format a professional email to the stakeholder. 
    If there are previous clarifications mentioned in the requirements, acknowledge them briefly and focus on the remaining questions.
    Ensure the email is polite and clearly explains why these answers are needed.
    
    IMPORTANT: End the email with a clear line:
    "Please provide your response here: http://localhost:8501/?view=respond&thread_id={thread_id}"
    """)

    response = llm.invoke(
        prompt.format(
            requirements=extracted_requirements,
            questions="\n".join(clarification_questions),
            thread_id=thread_id
        )
    )

    email_body = response.content

    # Step 2: Send Email
    try:
        msg = MIMEText(email_body)
        msg["Subject"] = "Requirement Clarification Needed"
        msg["From"] = smtp_config["sender"]
        msg["To"] = ", ".join(stakeholder_emails)

        print(f"DEBUG: Sending clarification email to: {stakeholder_emails}")
        server = smtplib.SMTP(smtp_config["server"], smtp_config["port"])
        server.starttls()
        server.login(smtp_config["sender"], smtp_config["password"])
        server.sendmail(smtp_config["sender"], stakeholder_emails, msg.as_string())
        server.quit()

        email_status = "Email Sent Successfully"
        print("DEBUG: Email sent successfully.")

    except Exception as e:
        email_status = f"Email Failed: {str(e)}"


    sessionId = get_session(thread_id)

    if sessionId:
        
        # Update MongoDB
        round_num = create_version(
            requirement_sessions_id=sessionId,
            clarification_questions=clarification_questions
        )
        
        update_session(
            session_id=sessionId,
            email_event={
                "round": round_num,
                "status": email_status
            }
        )

    # Step 3: Update State
    return {
        "email_status": email_status
    }