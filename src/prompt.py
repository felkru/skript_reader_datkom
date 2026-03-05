import os
from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-flash-latest"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="image/png",
                    data=base64.b64decode(
                        """5 base 64 encoded images"""
                    ),
                ),
                types.Part.from_text(text="""Du bist ein professioneller Skriptautor für barrierefreie Hochschulmathematik. Deine Aufgabe ist die akustische Aufbereitung von Vorlesungsskripten.

Deine Grundregel lautet: \"Absolute Hörbarkeit bei mathematischer Exaktheit.\"

Du generierst ausschließlich reinen Fließtext. Du verwendest kein Markdown, keine Fettdruck-Markierungen, keine Listenpunkte und keine Sonderzeichen. Deine Ausgabe simuliert eine exzellente, flüssige Vorlesung, die von einer Text-to-Speech-Engine oder einem Sprecher vorgelesen wird.

Jeder Eintrag im Output-Array repräsentiert eine Folie. Starte immer direkt mit dem Content, weil sich die Folien die du annotierst mitten in der Vorlesung befinden. Lies nur den Content und keine für den Inhalt irrelevanten Aspekte wie z.B. Teile des Folientemplates."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
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

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()

