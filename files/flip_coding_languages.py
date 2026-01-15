import os
import subprocess
from openai import OpenAI
from system_info import retrieve_system_info
import helpers

def build_compiler_help_message(system_info: str) -> str:
    return f"""
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

def ask_for_compiler_commands(client: OpenAI, model: str, system_info: str) -> str:
    message = build_compiler_help_message(system_info)
    print("fetching data...")
    response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": message}],
    )
    answer = response.choices[0].message.content or ""
    helpers.stream_text_response(client=client, prompt=answer, model=model)
    return answer

SYSTEM_PROMPT_CPP = """
    Your task is to convert Python code into high performance C++ code.
    Respond only with C++ code. Do not provide any explanation other than occasional comments.
    The C++ response needs to produce an identical output in the fastest possible time.
    """.strip()

def user_prompt_for(python_code: str, system_info: str, compile_command: str) -> str:
    return f"""
    Port this Python code to C++ with the fastest possible implementation that produces identical output in the least time.
    The system information is:
    {system_info}
    Your response will be written to a file called main.cpp and then compiled and executed; the compilation command is:
    {compile_command}
    Respond only with C++ code.
    Python code to port:
    {python_code}
    """.strip()

def messages_for(python_code: str, system_info: str, compile_command: str):
    return [
    {"role": "system", "content": SYSTEM_PROMPT_CPP},
    {"role": "user", "content": user_prompt_for(python_code, system_info, compile_command)},
    ]

def write_output(cpp: str, filename: str = "main.cpp") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(cpp)

def clean_cpp_fence(text: str) -> str:
    return text.replace("cpp", "").replace("", "").strip()

def port_python_to_cpp(
client: OpenAI,
    model: str,
    python_code: str,
    system_info: str,
    compile_command: str,
    ) -> str:
    reasoning_effort = "high" if "gpt" in model.lower() else None
    response = client.chat.completions.create(
    model=model,
    messages=messages_for(python_code, system_info, compile_command),
    reasoning_effort=reasoning_effort,
    )
    reply = response.choices[0].message.content or ""
    cpp = clean_cpp_fence(reply)
    write_output(cpp)
    return cpp


def run_python(code):
    print("\n\nRunning pyhon code...")
    globals = {"__builtins__": __builtins__}
    exec(code, globals)

import textwrap

def main() -> None:
    keys = helpers.load_keys()
    helpers.print_key_status(keys)
    helpers.clients = helpers.build_clients(keys)
    models = helpers.ModelConfig()

    system_info = retrieve_system_info()
    print(system_info)

    ask_for_compiler_commands(
        client=helpers.clients.openai,
        model=models.openai_model,
        system_info=system_info,
    )

    pi = textwrap.dedent("""
    import time

    def calculate(iterations, param1, param2):
        result = 1.0
        for i in range(1, iterations + 1):
            j = i * param1 - param2
            result -= (1 / j)
            j = i * param1 + param2
            result += (1 / j)
        return result

    start_time = time.time()
    result = calculate(200_000_000, 4, 1) * 4
    end_time = time.time()

    print(f"Result: {result:.12f}")
    print(f"Execution Time: {(end_time - start_time):.6f} seconds")
    """).strip()

    run_python(pi)

    # Change this according to the streamed output from the LLM according to your machine system
    compile_command = ["clang++", "-std=c++20", "-O3", "-march=native", "main.cpp", "-o", "main"]

    print("\n\nConvert to .cpp\n\n")
    port_python_to_cpp(
        client=helpers.clients.openai,
        model=models.openai_model,
        python_code=pi,
        system_info=system_info,
        compile_command=compile_command,
    )

    if not os.path.exists("main.cpp"):
        raise FileNotFoundError("main.cpp was not created")

    run_command = ["./main"]

    subprocess.run(compile_command, check=True, text=True, capture_output=True)
    print(subprocess.run(run_command, check=True, text=True, capture_output=True).stdout)


if __name__ == "__main__":
    main()


