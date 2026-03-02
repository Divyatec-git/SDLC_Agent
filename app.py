import streamlit as st
from graph import graph
from utils.document_loader import load_document
import os
import uuid
from dotenv import load_dotenv
from db.models.requirement_session import get_session_data_aggregated
from agents.code_generation_agent import code_generation_agent
load_dotenv()

st.set_page_config(page_title="SDLC Requirement Agent", layout="wide")
st.title("SDLC Requirement Extraction & Clarification Agent")

# Main UI
view = st.query_params.get("view", "main")
thread_id = st.query_params.get("thread_id", str(uuid.uuid4()))

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: Stakeholder Response Page
# ─────────────────────────────────────────────────────────────────────────────
if view == "respond":
    st.header("Stakeholder Clarification Response")
    config = {"configurable": {"thread_id": thread_id}}
    existing_state = graph.get_state(config)

    if not existing_state.values:
        st.error("Could not find the original request state. Please ensure the link is correct.")
        st.stop()

    st.write("Please review the requirements and clarification questions sent to your email.")
    with st.expander("Context from original request"):
        st.subheader("Extracted Requirements")
        st.write(existing_state.values.get("extracted_requirements"))
        st.subheader("Clarification Questions")
        for q in existing_state.values.get("clarification_questions", []):
            st.write(f"- {q}")

    response_text = st.text_area("Your Response / Clarifications", height=300)

    if st.button("Submit Response"):
        with st.spinner("AI is analyzing your feedback..."):
            graph.update_state(config, {"stakeholder_response": response_text})
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
            for q in result.get("clarification_questions", []):
                st.write(f"- {q}")

        st.info(f"Status: {result.get('email_status', 'Processed')}")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW: Main Agent Page
# ─────────────────────────────────────────────────────────────────────────────
else:
    config = {"configurable": {"thread_id": thread_id}}

    # Always read the REAL state from checkpointer
    current_graph_state = graph.get_state(config)
    next_node = current_graph_state.next[0] if current_graph_state.next else None
    state_values = current_graph_state.values

    # ── STEP 1: Upload Form ────────────────────────────────────────────────────
    st.header("Step 1: Upload Requirement Document")
    col1, col2 = st.columns(2)

    with col1:
        st.info(f"Session Thread ID: `{thread_id}`")
        uploaded_file = st.file_uploader("Upload Requirement Document")
        emails_input = st.text_input(
            "Enter Stakeholder Emails (comma separated)",
            placeholder="client1@example.com, client2@example.com"
        )
        run_agent = st.button("Process Document")

    if run_agent and uploaded_file and emails_input:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        document_text = load_document(uploaded_file.name)
        stakeholder_emails = [e.strip() for e in emails_input.split(",") if e.strip()]

        initial_state = {
            "raw_document": document_text,
            "extracted_requirements": "",
            "clarification_questions": [],
            "stakeholder_emails": stakeholder_emails,
            "email_status": "",
            "stakeholder_response": "",
            "is_clarified": False,
            "repo_url": "",
            "mermaid_diagram": "",
            "flowchart_image_url": "",
            "thread_id": thread_id,
            "smtp_config": {
                "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", 587)),
                "sender": os.getenv("SMTP_USERNAME", ""),
                "password": os.getenv("SMTP_PASSWORD", "")
            }
        }

        with st.spinner("⚙️ Processing requirements, creating repo and flowchart..."):
            result = graph.invoke(initial_state, config)

        # Refresh state after invocation
        current_graph_state = graph.get_state(config)
        next_node = current_graph_state.next[0] if current_graph_state.next else None
        state_values = current_graph_state.values

        with col2:
            st.header("Results")
            st.subheader("Extracted Requirements")
            st.write(result.get("extracted_requirements", ""))
            st.subheader("Email Status")
            email_status = result.get("email_status", "")
            if "Sent" in email_status or "Created" in email_status:
                st.success(email_status)
            else:
                st.info(email_status)
            if result.get("repo_url"):
                st.success(f"**[GitHub Repository]({result['repo_url']})**")
            if result.get("flowchart_image_url"):
                st.image(result["flowchart_image_url"], caption="Requirement Flowchart")

    # ── Show existing results if already processed ─────────────────────────────
    elif state_values and state_values.get("repo_url"):
        with col2:
            st.header("Results")
            st.write(state_values.get("extracted_requirements", ""))
            st.success(f"**[GitHub Repository]({state_values.get('repo_url')})**")
            if state_values.get("flowchart_image_url"):
                st.image(state_values["flowchart_image_url"], caption="Requirement Flowchart")

# Example input field
session_id = st.text_input("Enter Session ID")           
# Button
if st.button("Show Session Details"):
    if not session_id:
        st.warning("Please enter a session ID")
    else:
        session_data = get_session_data_aggregated(session_id)
        if not session_data:
            st.error("Session not found")
        else:
            st.success("Session Loaded Successfully ✅")

            # ----------------------------
            # Show Extracted Requirements
            # ----------------------------
            st.subheader("Extracted Requirements")
            st.write(session_data.get("extracted_requirements", "No requirements found"))

            # ----------------------------
            # Show Clarification Versions
            # ----------------------------
            versions = session_data.get("requirement_versions", [])

            if versions:
                st.subheader("Clarification Versions")

                for v in versions:
                    with st.expander(f"Version {v.get('version', 'N/A')}"):
                        st.write("Questions:")
                        st.write(v.get("clarification_questions", ""))

                        st.write("User Response:")
                        st.write(v.get("stakeholder_response", "Not submitted"))

                        st.write("Needs More Clarification:",
                                            v.get("needs_more_clarification", False))

            # ----------------------------
            # Show Final Output
            # ----------------------------
            final_output = session_data.get("final_output")

            if final_output and final_output.get("repo_url"):
                st.subheader("Final Output")

                st.success(
                    f"**[GitHub Repository]({final_output.get('repo_url')})**"
                )

                if final_output.get("flowchart_image_url"):
                    st.image(
                        final_output["flowchart_image_url"],
                        caption="Requirement Flowchart"
                    )
print("")

tech_stack = st.text_input("Enter Tech Stack")           

if st.button("Generate Code"):
    if not session_id:
        st.warning("Please enter a session ID")
    else:
        if not tech_stack:
            st.warning("Please enter a tech stack")
        
        session_data = get_session_data_aggregated(session_id)
        st.spinner("Generating code...")
        if not session_data:
            st.error("Session not found")
        else:
            st.success("Session Loaded Successfully ✅")
            final_output = session_data.get("final_output", {})
            repo_url = final_output.get("repo_url")

            if not repo_url:
                st.error("Repository URL not found in this session.")
            else:
                with st.spinner("Generating code..."):
                    result = code_generation_agent(
                        session_data.get("extracted_requirements", "No requirements found"), 
                        tech_stack, 
                        repo_url
                    )
                st.success(result["email_status"])