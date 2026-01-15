import os
import json
import sqlite3
import base64
from io import BytesIO
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

MODEL = "gpt-4.1-mini"
DB = "prices.db"

SYSTEM_MESSAGE = """
You are a helpful assistant for an Airline called FlightAI.
Give short, courteous answers, no more than 1 sentence.
Always be accurate. If you don't know the answer, say so.
""".strip()

PRICE_FUNCTION = {
    "name": "get_ticket_price",
    "description": "Get the price of a return ticket to the destination city.",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False,
    },
}
TOOLS = [{"type": "function", "function": PRICE_FUNCTION}]


def set_ticket_price(city: str, price: float) -> None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO prices (city, price)
            VALUES (?, ?)
            ON CONFLICT(city) DO UPDATE SET price = ?
            """,
            (city.lower(), price, price),
        )
        conn.commit()


def get_ticket_price(city: str) -> str:
    print(f"DATABASE TOOL CALLED: Getting price for {city}", flush=True)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price FROM prices WHERE city = ?", (city.lower(),))
        result = cursor.fetchone()
        return f"Ticket price to {city} is ${result[0]}" if result else "No price data available for this city"


def talker(client: OpenAI, message: str) -> bytes:
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=message,
    )
    return response.content


def artist(client: OpenAI, city: str) -> Image.Image:
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=(
            f"An image representing a vacation in {city}, showing tourist spots and everything unique "
            f"about {city}, in a vibrant pop-art style"
        ),
        size="1024x1024",
        n=1,
        response_format="b64_json",
    )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))


def handle_tool_calls_and_return_cities(message) -> tuple[list[dict], list[str]]:
    responses: list[dict] = []
    cities: list[str] = []

    for tool_call in message.tool_calls or []:
        if tool_call.function.name == "get_ticket_price":
            arguments = json.loads(tool_call.function.arguments)
            city = arguments.get("destination_city")
            if city:
                cities.append(city)
                price_details = get_ticket_price(city)
                responses.append(
                    {
                        "role": "tool",
                        "content": price_details,
                        "tool_call_id": tool_call.id,
                    }
                )

    return responses, cities


def chat(client: OpenAI, history: list[dict]) -> tuple[list[dict], bytes, Image.Image | None]:
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": SYSTEM_MESSAGE}] + history

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

    cities: list[str] = []
    image: Image.Image | None = None

    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        tool_responses, cities = handle_tool_calls_and_return_cities(message)
        messages.append(message)
        messages.extend(tool_responses)
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)

    reply = response.choices[0].message.content or ""
    history += [{"role": "assistant", "content": reply}]

    voice = talker(client, reply)

    if cities:
        image = artist(client, cities[0])

    return history, voice, image


def put_message_in_chatbot(message: str, history: list[dict]) -> tuple[str, list[dict]]:
    return "", history + [{"role": "user", "content": message}]


def init_db_and_seed() -> None:
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS prices (city TEXT PRIMARY KEY, price REAL)")
        conn.commit()

    ticket_prices = {"london": 799, "paris": 899, "tokyo": 1420, "sydney": 2999}
    for city, price in ticket_prices.items():
        set_ticket_price(city, price)


def build_ui(client: OpenAI) -> gr.Blocks:
    with gr.Blocks() as ui:
        with gr.Row():
            chatbot = gr.Chatbot(height=500, type="messages")
            image_output = gr.Image(height=500, interactive=False)
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        with gr.Row():
            message = gr.Textbox(label="Chat with our AI Assistant:")

        def _chat(history):
            return chat(client, history)

        message.submit(
            put_message_in_chatbot,
            inputs=[message, chatbot],
            outputs=[message, chatbot],
        ).then(
            _chat,
            inputs=chatbot,
            outputs=[chatbot, audio_output, image_output],
        )

    return ui


def main() -> int:
    load_dotenv(override=True)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")

    client = OpenAI()
    init_db_and_seed()

    ui = build_ui(client)
    ui.launch(inbrowser=True, auth=("eli", "123456"))
    return 0


if __name__ == "__main__":
    main()

# # Example inputs:
# # Auth:
# # username: eli
# # password 123456
#
# # Hi there
# # I'd like to go on a trip
# # To London Please