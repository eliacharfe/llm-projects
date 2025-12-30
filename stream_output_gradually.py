import os
from dotenv import load_dotenv
from openai import OpenAI
import sys
import time

MODEL_GPT = 'gpt-4o-mini'
MODEL_LLAMA = 'llama3.2'

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key) > 10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")


def explain_technical_question(model, code) -> str:
    user_prompt_question = f"Please explain what this code does and why:\n\n{code}"

    print(f"Generating explanation to the code: {code} using model {model}")

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": user_prompt_question}
        ]
    )
    result = response.choices[0].message.content
    return result


def _in_notebook() -> bool:
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


def stream_text_response(
        prompt: str = "Tell me a fun fact about space in 2-3 sentences.",
        model: str = "gpt-4.1-mini",
        chunk_delay_sec: float = 0.02,
):
    stream = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    response = ""
    is_nb = _in_notebook()

    if is_nb:
        from IPython.display import Markdown, display, update_display
        display_handle = display(Markdown(""), display_id=True)

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            response += delta
            update_display(Markdown(response), display_id=display_handle.display_id)

            if chunk_delay_sec > 0:
                time.sleep(chunk_delay_sec)

        return response

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if not delta:
            continue
        response += delta
        sys.stdout.write(delta)
        sys.stdout.flush()

        if chunk_delay_sec > 0:
            time.sleep(chunk_delay_sec)

    print()
    return response


openai = OpenAI()

text = explain_technical_question(MODEL_GPT, "yield from {book.get('author') for book in books if book.get('author')}")
print(stream_text_response(text, model=MODEL_GPT))

print("----------------------")
print("----------------------")

# Get Llama 3.2 to answer

OLLAMA_BASE_URL = "http://localhost:11434/v1"

openai = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')

text = explain_technical_question(MODEL_LLAMA, "yield from {book.get('author') for book in books if book.get('author')}")
print(stream_text_response(text, model=MODEL_LLAMA))