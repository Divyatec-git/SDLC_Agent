import streamlit as st
from graph import graph
from utils.document_loader import load_document
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SDLC Requirement Agent", layout="wide")
st.title("SDLC Requirement Extraction & Clarification Agent")

# Main UI
view = st.query_params.get("view", "main")
thread_id = st.query_params.get("thread_id", str(uuid.uuid4()))

if view == "respond":
    st.header("Stakeholder Clarification Response")
    
    # Retrieve existing state for this thread
    config = {"configurable": {"thread_id": thread_id}}
    existing_state = graph.get_state(config)
    
    if not existing_state.values:
        st.error("Could not find the original request state. Please ensure the link is correct.")
        st.stop()

    st.write("Please review the requirements and clarification questions sent to your email.")
    
    # Show context to the stakeholder
    with st.expander("Context from original request"):
        st.subheader("Extracted Requirements")
        st.write(existing_state.values.get("extracted_requirements"))
        st.subheader("Clarification Questions")
        for q in existing_state.values.get("clarification_questions", []):
            st.write(f"- {q}")

    response_text = st.text_area("Your Response / Clarifications", height=300)
    
    if st.button("Submit Response"):
        with st.spinner("AI is analyzing your feedback..."):
            # Update state with the response
            graph.update_state(config, {"stakeholder_response": response_text})
            
            # Resume graph execution
            result = graph.invoke(None, config)
            
            st.write("---")
            st.header("Results")
            
            if result.get("repo_url"):
                st.success("✅ Requirements Clarified & Project Initialized!")
                st.write(f"### [Project Repository]({result['repo_url']})")
                
                if result.get("flowchart_image_url"):
                    st.subheader("Requirement Flowchart")
                    st.image(result["flowchart_image_url"], use_container_width=True)
                
                st.balloons()
            elif not result.get("is_clarified"):
                st.warning("⚠️ Some points still need clarification. A follow-up email has been sent.")
                st.subheader("Remaining Questions")
                for q in result.get("clarification_questions", []):
                    st.write(f"- {q}")
            
            st.info(f"Final Status: {result.get('email_status', 'Processed')}")

else:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Input")
        st.info(f"Session Thread ID: `{thread_id}`")
        # Upload Document
        uploaded_file = st.file_uploader("Upload Requirement Document")

        # Stakeholder Emails Input
        emails_input = st.text_input(
            "Enter Stakeholder Emails (comma separated)",
            placeholder="client1@example.com, client2@example.com"
        )

        run_agent = st.button("Process Document")

    if run_agent and uploaded_file and emails_input:
        # Save uploaded file
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        document_text = load_document(uploaded_file.name)

        # Convert email string → list
        stakeholder_emails = [
            email.strip()
            for email in emails_input.split(",")
            if email.strip()
        ]

        state = {
            "raw_document": document_text,
            "extracted_requirements": "",
            "clarification_questions": [],
            "stakeholder_emails": stakeholder_emails,
            "email_status": "",
            "stakeholder_response": "",
            "is_clarified": False,
            "repo_url": "",
            "smtp_config": {
                "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", 587)),
                "sender": os.getenv("SMTP_USERNAME", ""),
                "password": os.getenv("SMTP_PASSWORD", "")
            }
        }

        config = {"configurable": {"thread_id": thread_id}}

        with st.spinner("Processing..."):
            result = graph.invoke(state, config)

        with col2:
            st.header("Results")
            st.subheader("Extracted Requirements")
            st.write(result["extracted_requirements"])

            st.subheader("Clarification Questions")
            for q in result["clarification_questions"]:
                st.write("- ", q)

            st.subheader("Email Status")
            if "Successfully" in result["email_status"]:
                st.success(result["email_status"])
            else:
                st.error(result["email_status"])