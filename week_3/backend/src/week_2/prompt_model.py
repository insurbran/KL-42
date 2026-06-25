import os
import sys
from google import genai
from dotenv import load_dotenv
import ollama

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_client = ollama.Client(host=OLLAMA_HOST)

OLLAMA_MODELS = ["llama3.1", "phi3", "deepseek-r1:1.5b"]
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"]


def prompt_model(model: str, prompt: str) -> str:
    try:
        if model in OLLAMA_MODELS:
            response = ollama_client.chat(
                model=model, messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]

        elif model in GEMINI_MODELS:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text

        else:
            return f"[Error] Unknown model: {model}"

    except Exception as e:
        return f"[Error] {e}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: uv run prompt_model.py <model> <prompt>")
        import sys

        sys.exit()

    model = sys.argv[1]
    prompt = sys.argv[2]

    response = prompt_model(model, prompt)
    print("\n--- RESPONSE ---\n")
    print(response)
