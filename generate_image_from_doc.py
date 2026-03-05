import os
import base64
from openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from db.models.requirement_session import get_session_data_aggregated
from db.models.final_output import update_infographic_url
load_dotenv()

# --------------------------------
# CONFIG
# --------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OUTPUT_FOLDER = "generated_images"

session_id = "93001338-ba44-4281-89e7-cd59746a554c"
session_data = get_session_data_aggregated(session_id)
document_context = session_data.get("extracted_requirements")


update_infographic_url(session_data.get("_id"), "generated_images/infographic_69a97ffd6e43dd005e734f69.png")

exit()
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --------------------------------
# OPENROUTER LLM (Prompt Generator)
# --------------------------------
llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    temperature=0.7
)
prompt_template = ChatPromptTemplate.from_template(
"""
Create a visual prompt for generating an infographic from the following document.

Document:
{context}

Generate the infographic in an Excalidraw-style hand-drawn diagram with sketchy lines, thin strokes, and a whiteboard background.

Organize the information into multiple rounded boxes connected with arrows. Each box should contain a short title, a simple line icon, and 3–5 short bullet points summarizing the key ideas.

Use minimal text, simple shapes, and a few soft accent colors like light blue or sage green.

Return only the final prompt for the image generator.
"""
)

chain = prompt_template | llm
response = chain.invoke({"context": document_context})

image_prompt = response.content

print("\nGenerated Prompt:\n")
print(image_prompt)

# --------------------------------
# OPENROUTER IMAGE GENERATION
# --------------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

image_response = client.chat.completions.create(
    model="google/gemini-3.1-flash-image-preview",
    messages=[
        {
            "role": "user",
            "content": image_prompt
        }
    ],
    extra_body={"modalities": ["image", "text"]}
)

# --------------------------------
# SAVE IMAGE
# --------------------------------
msg = image_response.choices[0].message

if msg.images:
    for i, img in enumerate(msg.images):

        data_url = img["image_url"]["url"]
        base64_data = data_url.split(",")[1]

        image_bytes = base64.b64decode(base64_data)

        file_path = os.path.join(
            OUTPUT_FOLDER,
            f"infographic_{i}.png"
        )

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        print(f"\nImage saved to: {file_path}")