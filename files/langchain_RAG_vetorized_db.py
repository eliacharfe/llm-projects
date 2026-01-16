from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import glob
import tiktoken
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import gradio as gr
import helpers

MODEL = "gpt-4.1-nano"
DB_NAME = "vector_db"

SYSTEM_PROMPT_TEMPLATE = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
Context:
{context}
"""

def scan_knowledge_base_files(pattern: str = "knowledge-base/**/*.md") -> list[str]:
    files = glob.glob(pattern, recursive=True)
    print(f"Found {len(files)} files in the knowledge base")
    return files


def print_kb_size_and_tokens(files: list[str], model: str) -> None:
    entire = ""
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            entire += f.read() + "\n\n"

    print(f"Total characters in knowledge base: {len(entire):,}")

    encoding = tiktoken.encoding_for_model(model)
    token_count = len(encoding.encode(entire))
    print(f"Total tokens for {model}: {token_count:,}")


def load_all_markdown_documents(base_dir: str = "knowledge-base") -> list:
    folders = glob.glob(os.path.join(base_dir, "*"))
    documents = []

    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)

    print(f"Loaded {len(documents)} documents")
    return documents

def split_documents(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)

    print(f"Divided into {len(chunks)} chunks")
    # if chunks:
    #     print(f"First chunk:\n\n{chunks[0]}")
    return chunks

def main() -> None:
    load_dotenv(override=True)
    keys = helpers.load_keys()
    helpers.print_key_status(keys)
    helpers.clients = helpers.build_clients(keys)

    files = scan_knowledge_base_files()
    print_kb_size_and_tokens(files, MODEL)

    documents = load_all_markdown_documents()
    chunks = split_documents(documents)

    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    if os.path.exists(DB_NAME):
        Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

    vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=DB_NAME)
    print(f"Vectorstore created with {vectorstore._collection.count()} documents")

    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    llm = ChatOpenAI(temperature=0, model_name=MODEL)

    # print("\nretriever invoke:")
    # print(retriever.invoke("Who is Avery?"))
    # print("\n--------------------\n")

    def answer_question(question: str, history):
        docs = retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
        return response.content

    print("\n---------------------")
    print(answer_question("Who is Avery Lancaster?", []).replace(". ", ".\n"))

    gr.ChatInterface(answer_question).launch(inbrowser=True)


if __name__ == "__main__":
    main()
