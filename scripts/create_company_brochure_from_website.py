
import os
import json
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from openai import OpenAI
from bs4 import BeautifulSoup
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


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


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt

def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling {MODEL}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Found {len(links['links'])} relevant links")
    return links

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if api_key and api_key.startswith('sk-proj-') and len(api_key) > 10:
    print("API key looks good so far")
else:
    print("There might be a problem with your API key? Please visit the troubleshooting notebook!")

MODEL = 'gpt-5-nano'
openai = OpenAI()

links = fetch_website_links("https://edwarddonner.com")
# links = fetch_website_links("https://eliacharfeig.com")
# print(links)

#---------------

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

# print(get_links_user_prompt("https://edwarddonner.com"))
# # print(get_links_user_prompt("https://eliacharfeig.com"))
#
# print("-------------")
#
# print(select_relevant_links("https://edwarddonner.com"))
# # print(select_relevant_links("https://eliacharfeig.com"))
# print(select_relevant_links("https://huggingface.co"))

print("-------------")

# print(fetch_page_and_all_relevant_links("https://huggingface.co"))

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt

# print(get_brochure_user_prompt("HuggingFace", "https://huggingface.co"))

def create_brochure(company_name, url):
    response = openai.chat.completions.create(model="gpt-4.1-mini", messages=[
        {"role": "system", "content": brochure_system_prompt},
        {"role": "user", "content": get_brochure_user_prompt(company_name, url)},
    ])
    result = response.choices[0].message.content
    display(result)

# print(create_brochure("HuggingFace", "https://huggingface.co"))

# def stream_brochure(company_name, url):
#     stream = openai.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[
#             {"role": "system", "content": brochure_system_prompt},
#             {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
#           ],
#         stream=True
#     )
#     response = ""
#     display_handle = display(Markdown(""), display_id=True)
#     for chunk in stream:
#         response += chunk.choices[0].delta.content or ''
#         update_display(Markdown(response), display_id=display_handle.display_id)

import sys

def _in_notebook() -> bool:
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is None:
            return False
        # ZMQInteractiveShell == Jupyter notebook/lab
        return ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


def stream_brochure(company_name, url):
    stream = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )

    response = ""
    is_nb = _in_notebook()

    if is_nb:
        from IPython.display import Markdown, display, update_display
        display_handle = display(Markdown(""), display_id=True)

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            response += delta
            update_display(Markdown(response), display_id=display_handle.display_id)
        return response

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        response += delta
        sys.stdout.write(delta)
        sys.stdout.flush()

    print()
    return response


print(stream_brochure("HuggingFace", "https://huggingface.co"))
# print(stream_brochure("Eliachar Feig", "https://eliacharfeig.com"))