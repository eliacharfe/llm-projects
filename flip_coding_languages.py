import os
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from system_info import retrieve_system_info
from helpers import stream_text_response


load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
grok_api_key = os.getenv('GROK_API_KEY')

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set (and this is optional)")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:2]}")
else:
    print("Google API Key not set (and this is optional)")

if grok_api_key:
    print(f"Grok API Key exists and begins {grok_api_key[:4]}")
else:
    print("Grok API Key not set (and this is optional)")




openai = OpenAI()

anthropic_url = "https://api.anthropic.com/v1/"
gemini_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
grok_url = "https://api.x.ai/v1"

anthropic = OpenAI(api_key=anthropic_api_key, base_url=anthropic_url)
gemini = OpenAI(api_key=google_api_key, base_url=gemini_url)
grok = OpenAI(api_key=grok_api_key, base_url=grok_url)

OPENAI_MODEL = "gpt-5"
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
GROK_MODEL = "grok-4"
GEMINI_MODEL = "gemini-2.5-pro"


system_info = retrieve_system_info()
print(system_info)

message = f"""
Here is a report of the system information for my computer.
I want to run a C++ compiler to compile a single C++ file called main.cpp and then execute it in the simplest way possible.
Please reply with whether I need to install any C++ compiler to do this. If so, please provide the simplest step by step instructions to do so.

If I'm already set up to compile C++ code, then I'd like to run something like this in Python to compile and execute the code:
```python
compile_command = # something here - to achieve the fastest possible runtime performance
compile_result = subprocess.run(compile_command, check=True, text=True, capture_output=True)
run_command = # something here
run_result = subprocess.run(run_command, check=True, text=True, capture_output=True)
return run_result.stdout
```
Please tell me exactly what I should use for the compile_command and run_command.

System information:
{system_info}
"""

print("fetching data...")
response = openai.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "user", "content": message}])
# print(response.choices[0].message.content)
stream_text_response(client=openai, prompt=response.choices[0].message.content, model=OPENAI_MODEL)


system_prompt = """
Your task is to convert Python code into high performance C++ code.
Respond only with C++ code. Do not provide any explanation other than occasional comments.
The C++ response needs to produce an identical output in the fastest possible time.
"""

def user_prompt_for(python):
    return f"""
Port this Python code to C++ with the fastest possible implementation that produces identical output in the least time.
The system information is:
{system_info}
Your response will be written to a file called main.cpp and then compiled and executed; the compilation command is:
{compile_command}
Respond only with C++ code.
Python code to port:

```python
{python}
```
"""


def messages_for(python):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(python)}
    ]


def write_output(cpp):
    with open("main.cpp", "w", encoding="utf-8") as f:
        f.write(cpp)

def port(client, model, python):
    reasoning_effort = "high" if 'gpt' in model else None
    response = client.chat.completions.create(model=model, messages=messages_for(python), reasoning_effort=reasoning_effort)
    reply = response.choices[0].message.content
    reply = reply.replace('```cpp','').replace('```','')
    write_output(reply)

pi = """
import time

def calculate(iterations, param1, param2):
    result = 1.0
    for i in range(1, iterations+1):
        j = i * param1 - param2
        result -= (1/j)
        j = i * param1 + param2
        result += (1/j)
    return result

start_time = time.time()
result = calculate(200_000_000, 4, 1) * 4
end_time = time.time()

print(f"Result: {result:.12f}")
print(f"Execution Time: {(end_time - start_time):.6f} seconds")
"""

def run_python(code):
    globals = {"__builtins__": __builtins__}
    exec(code, globals)

run_python(pi)

port(openai, OPENAI_MODEL, pi)




# AFTER main.cpp is created UNCOMMENT run the following commands:


# compile_command = ["clang++", "-std=c++17", "-Ofast", "-mcpu=native", "-flto=thin", "-fvisibility=hidden", "-DNDEBUG", "main.cpp", "-o", "main"]
# run_command = ["./main"]
#
# def compile_and_run():
#     subprocess.run(compile_command, check=True, text=True, capture_output=True)
#     print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
#     print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
#     print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)
#
# compile_and_run()