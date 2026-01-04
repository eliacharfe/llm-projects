import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup
import requests


MODEL = "gpt-5-nano"

SYSTEM_PROMPT = """
You are a helpful assistant that analyzes the contents of a website,
and provides a short summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
""".strip()

USER_PROMPT_PREFIX = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

""".lstrip()


def load_api_key() -> str | None:
    load_dotenv(override=True)
    return os.getenv("OPENAI_API_KEY")


def validate_api_key(api_key: str | None) -> bool:
    if not api_key:
        print(
            "No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!"
        )
        return False
    if not api_key.startswith("sk-proj-"):
        print(
            "An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook"
        )
        return False

    print("API key found and looks good so far!")
    return True


def build_messages(website_text: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_PREFIX + website_text},
    ]


def fetch_website_contents(url: str, request_headers: dict[str, str], limit: int = 2_000) -> str:
    """
    Return the title and contents of the website at the given url;
    truncate to `limit` characters as a sensible limit.
    """
    resp = requests.get(url, headers=request_headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"

    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""

    return (title + "\n\n" + text)[:limit]


def summarize_url(client: OpenAI, url: str, request_headers: dict[str, str], model: str = MODEL) -> str:
    website = fetch_website_contents(url, request_headers=request_headers)
    response = client.chat.completions.create(
        model=model,
        messages=build_messages(website),
    )
    return response.choices[0].message.content or ""


def display_summary(client: OpenAI, url: str, request_headers: dict[str, str]) -> None:
    summary = summarize_url(client, url, request_headers=request_headers)
    print(summary)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    url = argv[0] if argv else "https://edwarddonner.com"

    api_key = load_api_key()
    if not validate_api_key(api_key):
        return 1

    request_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0 Safari/537.36"
    }

    client = OpenAI(api_key=api_key)

    display_summary(client, url, request_headers=request_headers)
    return 0


if __name__ == "__main__":
    main()


# message = "Hello, GPT! This is my first ever message to you! Hi!"
#
# messages = [{"role": "user", "content": message}]
#
# # print(messages)
#
# response = openai.chat.completions.create(model="gpt-5-nano", messages=messages)
# print(response.choices[0].message.content)


# response = openai.chat.completions.create(model="gpt-5-nano",
#                                           messages=[{"role": "user", "content": "Tell me a fun fact"}])
#
# print(response.choices[0].message.content)


