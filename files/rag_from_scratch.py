import gradio as gr
from dotenv import load_dotenv
from pro_implementation.ingest import run_ingestion

load_dotenv(override=True)
answer_question = None

def format_context(context):
    result = "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for doc in context:
        result += f"<span style='color: #ff7800;'>Source: {doc.metadata['source']}</span>\n\n"
        result += doc.page_content + "\n\n"
    return result


def chat(history):
    global answer_question
    last_message = history[-1]["content"]
    prior = history[:-1]

    answer, context = answer_question(last_message, prior)
    history.append({"role": "assistant", "content": answer})
    return history, format_context(context)


def main():
    from chromadb import PersistentClient
    from pathlib import Path

    DB_NAME = str(Path(__file__).parent / "preprocessed_db")
    collection_name = "docs"

    chroma = PersistentClient(path=DB_NAME)
    existing_collections = {c.name for c in chroma.list_collections()}

    should_ingest = True
    if collection_name in existing_collections:
        try:
            collection = chroma.get_collection(collection_name)
            if collection.count() > 0:
                should_ingest = False
        except Exception:
            should_ingest = True

    if should_ingest:
        print("Starting knowledge base ingestion...")
        run_ingestion()
        print("Ingestion finished.")
    else:
        print("Existing vector DB found. Skipping ingestion.")

    print("Launching UI...")

    from pro_implementation.answer import answer_question as _answer_question
    global answer_question
    answer_question = _answer_question

    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Insurellm Expert Assistant", theme=theme) as ui:
        gr.Markdown("# 🏢 Insurellm Expert Assistant\nAsk me anything about Insurellm!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    height=600,
                    type="messages",
                    show_copy_button=True,
                )
                message = gr.Textbox(
                    placeholder="Ask anything about Insurellm...",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(
            chat,
            inputs=chatbot,
            outputs=[chatbot, context_markdown],
        )

    ui.launch(inbrowser=True, show_error=True)


if __name__ == "__main__":
    main()

