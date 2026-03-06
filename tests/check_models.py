import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PRIMARY_MODEL = "anthropic/claude-3.5-sonnet"
FALLBACK_MODEL = "openai/gpt-4o-mini"

def check_model(model_name):
    print(f"\n--- Checking Model: {model_name} ---")
    try:
        llm = ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            temperature=0
        )
        response = llm.invoke("Say 'Success' if you can read this.")
        print(f"Response: {response.content}")
        return True
    except Exception as e:
        print(f"Error checking {model_name}: {e}")
        return False

if __name__ == "__main__":
    primary_ok = check_model(PRIMARY_MODEL)
    fallback_ok = check_model(FALLBACK_MODEL)
    
    print("\n--- Summary ---")
    print(f"Primary ({PRIMARY_MODEL}): {'✅' if primary_ok else '❌'}")
    print(f"Fallback ({FALLBACK_MODEL}): {'✅' if fallback_ok else '❌'}")
