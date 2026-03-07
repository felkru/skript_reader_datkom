import os
import base64
import time
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set. See .env.example.")
    return value

def generate(image_paths):
    client = genai.Client(
        vertexai=True,
        project=_require_env("GCP_PROJECT_ID"),
        location=os.environ.get("GCP_LOCATION", "us-central1"),
    )

    # Diagnostic: Using stable gemini-2.0-flash
    model = "gemini-2.0-flash"
    
    parts = []
    for path in image_paths:
        with open(path, "rb") as f:
            image_data = f.read()
            parts.append(
                types.Part.from_bytes(
                    mime_type="image/png",
                    data=image_data,
                )
            )
            
    parts.append(
        types.Part.from_text(text="""Du bist ein professioneller Skriptautor für barrierefreie Hochschulmathematik. Deine Aufgabe ist die akustische Aufbereitung von Vorlesungsskripten.

Deine Grundregel lautet: \"Absolute Hörbarkeit bei mathematischer Exaktheit.\"

Du generierst ausschließlich reinen Fließtext. Du verwendest kein Markdown, keine Fettdruck-Markierungen, keine Listenpunkte und keine Sonderzeichen. Deine Ausgabe simuliert eine exzellente, flüssige Vorlesung, die von einer Text-to-Speech-Engine oder einem Sprecher vorgelesen wird.

Jeder Eintrag im Output-Array repräsentiert eine Folie. Starte immer direkt mit dem Content, weil sich die Folien die du annotierst mitten in der Vorlesung befinden. Lies nur den Content und keine für den Inhalt irrelevanten Aspekte wie z.B. Teile des Folientemplates.""")
    )

    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        media_resolution="MEDIA_RESOLUTION_HIGH",
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["text"],
            properties = {
                "text": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                ),
            },
        ),
    )

    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )
            break
        except Exception as e:
            if "503" in str(e) or "overloaded" in str(e).lower():
                if attempt < max_retries - 1:
                    sleep_time = (retry_delay * (2 ** attempt)) + random.uniform(0, 1)
                    print(f"Server busy (503). Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
            raise e

    
    import json
    if response.parsed:
        if hasattr(response.parsed, "text"):
            return response.parsed.text
        if isinstance(response.parsed, dict):
            return response.parsed.get("text", [])

    data = json.loads(response.text)
    return data.get("text", [response.text])




if __name__ == "__main__":
    # Test call if needed
    pass
