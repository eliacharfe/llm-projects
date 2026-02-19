import os
import glob
from dotenv import load_dotenv
from pathlib import Path
import gradio as gr
from openai import OpenAI
import helpers

SYSTEM_PREFIX = """
You represent Insurellm, the Insurance Tech company.
You are an expert in answering questions about Insurellm; its employees and its products.
You are provided with additional context that might be relevant to the user's question.
Give brief, accurate answers. If you don't know the answer, say so.

Relevant context:
"""

def get_relevant_context(message, knowledge):
    text = ''.join(ch for ch in message if ch.isalpha() or ch.isspace())
    words = text.lower().split()
    return [knowledge[word] for word in words if word in knowledge]

def additional_context(message, knowledge):
    relevant_context = get_relevant_context(message, knowledge)
    if not relevant_context:
        result = "There is no additional context relevant to the user's question."
    else:
        result = "The following additional context might be relevant in answering the user's question:\n\n"
        result += "\n\n".join(relevant_context)
    return result

# def chat(message, history):
#     keys = helpers.load_keys()
#     helpers.print_key_status(keys)
#     helpers.clients = helpers.build_clients(keys)
#     system_message = SYSTEM_PREFIX + additional_context(message)
#     messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
#     response = helpers.clients.openai.chat.completions.create(model=helpers.ModelConfig.openai_model, messages=messages)
#     return response.choices[0].message.content
def make_chat(knowledge, client, model):
    def chat(message, history):
        system_message = SYSTEM_PREFIX + additional_context(message, knowledge)
        messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content or ""
    return chat


def main() -> None:
    keys = helpers.load_keys()
    helpers.print_key_status(keys)
    helpers.clients = helpers.build_clients(keys)
    models = helpers.ModelConfig()

    knowledge = {}

    filenames = glob.glob("knowledge-base/employees/*")

    for filename in filenames:
        name = Path(filename).stem.split(' ')[-1]
        with open(filename, "r", encoding="utf-8") as f:
            knowledge[name.lower()] = f.read()

    print(knowledge)

    print("\n\nPrint single employee by last name:\n")
    print(knowledge["lancaster"])

    filenames = glob.glob("knowledge-base/products/*")

    for filename in filenames:
        name = Path(filename).stem
        with open(filename, "r", encoding="utf-8") as f:
            knowledge[name.lower()] = f.read()

    print(knowledge.keys())

    print("\n---------------------------------------")
    print(get_relevant_context("Who is lancaster?", knowledge))
    print("---------------------------------------\n")

    print("\n---------------------------------------")
    print(get_relevant_context("Who is Lancaster and what is carllm?", knowledge))
    print("---------------------------------------\n")

    print("\n---------------------------------------")
    print(additional_context("Who is Alex Lancaster?", knowledge))
    print("---------------------------------------\n")

    chat_fn = make_chat(knowledge, helpers.clients.openai, models.openai_model)
    gr.ChatInterface(chat_fn, type="messages").launch(inbrowser=True)

if __name__ == "__main__":
    main()

