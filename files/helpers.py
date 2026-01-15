import sys
import time
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI


@dataclass(frozen=True)
class ApiKeys:
    openai: Optional[str]
    anthropic: Optional[str]
    google: Optional[str]
    grok: Optional[str]


@dataclass(frozen=True)
class ModelConfig:
    openai_model: str = "gpt-5"
    claude_model: str = "claude-sonnet-4-5-20250929"
    grok_model: str = "grok-4"
    gemini_model: str = "gemini-2.5-pro"


@dataclass(frozen=True)
class ClientBundle:
    openai: OpenAI
    anthropic: Optional[OpenAI]
    gemini: Optional[OpenAI]
    grok: Optional[OpenAI]


def load_keys() -> ApiKeys:
    load_dotenv(override=True)
    return ApiKeys(
        openai=os.getenv("OPENAI_API_KEY"),
        anthropic=os.getenv("ANTHROPIC_API_KEY"),
        google=os.getenv("GOOGLE_API_KEY"),
        grok=os.getenv("GROK_API_KEY"),
    )


def print_key_status(keys: ApiKeys) -> None:
    if keys.openai:
        print(f"OpenAI API Key exists and begins {keys.openai[:8]}")
    else:
        print("OpenAI API Key not set")

    if keys.anthropic:
        print(f"Anthropic API Key exists and begins {keys.anthropic[:7]}")
    else:
        print("Anthropic API Key not set (and this is optional)")

    if keys.google:
        print(f"Google API Key exists and begins {keys.google[:2]}")
    else:
        print("Google API Key not set (and this is optional)")

    if keys.grok:
        print(f"Grok API Key exists and begins {keys.grok[:4]}")
    else:
        print("Grok API Key not set (and this is optional)")


def build_clients(keys: ApiKeys) -> ClientBundle:
    openai_client = OpenAI(api_key=keys.openai) if keys.openai else OpenAI()

    anthropic = (
        OpenAI(api_key=keys.anthropic, base_url="https://api.anthropic.com/v1/")
        if keys.anthropic
        else None
    )
    gemini = (
        OpenAI(api_key=keys.google, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        if keys.google
        else None
    )
    grok = (
        OpenAI(api_key=keys.grok, base_url="https://api.x.ai/v1")
        if keys.grok
        else None
    )

    return ClientBundle(openai=openai_client, anthropic=anthropic, gemini=gemini, grok=grok)


def in_notebook() -> bool:
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
    is_nb = in_notebook()

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