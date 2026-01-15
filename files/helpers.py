import sys
import time
from openai import OpenAI

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