import os
from dotenv import load_dotenv
from IPython.display import Markdown, display
from openai import OpenAI
from bs4 import BeautifulSoup
import requests

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

system_prompt = """
You are a helpful assistant that analyzes the contents of a website,
and provides a short summary, ignoring text that might be navigation related.
Respond in markdown. Do not wrap the markdown in a code block - respond just with the markdown.
"""

user_prompt_prefix = """
Here are the contents of a website.
Provide a short summary of this website.
If it includes news or announcements, then summarize these too.

"""

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website}
    ]

def summarize(url):
    website = fetch_website_contents(url)
    response = openai.chat.completions.create(
        model = "gpt-5-nano",
        messages = messages_for(website)
    )
    return response.choices[0].message.content

def display_summary(url):
    summary = summarize(url)
    print(summary)

def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]



openai = OpenAI()

# display_summary("https://eliacharfeig.com")
print(display_summary("https://edwarddonner.com"))

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


