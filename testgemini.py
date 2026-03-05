from openai import OpenAI
import base64
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model="google/gemini-3.1-flash-image-preview",
    messages=[
        {
            "role": "user",
            "content": "Generate a beautiful sunset over mountains"
        }
    ],
    extra_body={"modalities": ["image", "text"]}
)

response = response.choices[0].message

if response.images:
    for i, image in enumerate(response.images):

        image_url = image['image_url']['url']  # data:image/png;base64,...

        # Remove the prefix
        base64_data = image_url.split(",")[1]

        # Decode Base64
        image_bytes = base64.b64decode(base64_data)

        # Save file
        file_path = f"generated_image_{i}.png"
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        print(f"Saved image to {file_path}")