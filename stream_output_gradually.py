import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI

MODEL_GPT = "gpt-4o-mini"
MODEL_LLAMA = "llama3.2"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


def check_api_key() -> str | None:
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key and api_key.startswith("sk-proj-") and len(api_key) > 10:
        print("API key looks good so far")
    else:
        print("There might be a problem with your API key? Please visit the troubleshooting notebook!")

    return api_key


def explain_technical_question(client: OpenAI, model: str, code: str) -> str:
    user_prompt_question = f"Please explain what this code does and why:\n\n{code}"
    print(f"Generating explanation to the code: {code} using model {model}")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_prompt_question}],
    )
    return response.choices[0].message.content or ""


def _in_notebook() -> bool:
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


def stream_text_response(
    client: OpenAI,
    prompt: str,
    model: str,
    chunk_delay_sec: float = 0.02,
) -> str:
    stream = client.chat.completions.create(
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


def run_explain_and_stream(client: OpenAI, model: str, code: str) -> None:
    explanation = explain_technical_question(client, model, code)
    streamed = stream_text_response(client, explanation, model=model)
    if _in_notebook():
        print(streamed)


def main() -> int:
    api_key = check_api_key()

    code_snippet = "yield from {book.get('author') for book in books if book.get('author')}"

    # OpenAI
    openai_client = OpenAI(api_key=api_key)
    run_explain_and_stream(openai_client, MODEL_GPT, code_snippet)

    print("\n----------------------\n----------------------\n")

    # Ollama (Llama 3.2)
    ollama_client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    run_explain_and_stream(ollama_client, MODEL_LLAMA, code_snippet)

    return 0


if __name__ == "__main__":
    main()
