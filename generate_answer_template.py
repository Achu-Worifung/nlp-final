#!/usr/bin/env python3
"""
Generate a placeholder answer file that matches the expected auto-grader format.

Replace the placeholder logic inside `build_answers()` with your own agent loop
before submitting so the ``output`` fields contain your real predictions.

Reads the input questions from cse_476_final_project_test_data.json and writes
an answers JSON file where each entry contains a string under the "output" key.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from contextlib import redirect_stdout
import io
import re
from dotenv import load_dotenv
from ddgs import DDGS 
import requests

INPUT_PATH = Path("cse_476_final_project_test_data.json")
OUTPUT_PATH = Path("cse_476_final_project_answers.json")
API_KEY="cse476"
API_BASE="http://10.4.58.53:41701/v1"
MODEL="bens_model"   
pre_analogical_sys_prompt = """You are a careful assistant. 
                                First think through the problem step by step before answering. 
                                Provide detail explanation of every step before providing the final answer."""
analogical_prompt_template = """Follow this steps to answer the question:
                                1. Generate a similar example question along with its answer.
                                2. Use this example to help you answer the main question.
                                Here are the tools at your disposal:
                                - Google Search: useful for when you need to look up information about current events, people, places, or any other topic. Use this tool by saying "Google Search: <your query> iexample: Google Search: who is the most handsome man in the world?"
                                - Python Executioner: useful for when you need to perform calculations, data analysis, or any other task that requires executing Python code. Use this tool by saying "Python Executioner: <your python code>" iexample: Python Executioner: print(2+2)
                                PROVIDE YOU FINAL ANWSER WITH EVERY STEP OF YOUR REASONING.
                                """ 
self_refine_sys_prompt =     """You are a Meticolous grader.Your goal is to verify the correctness of answers to a given question."""
self_refine_prompt_temp =  """
                            You are a Quality Assurance Auditor. 
                            1. Check the proposed answer for logical flaws or missed constraints.
                            2. If the answer is correct, repeat it inside <answer> tags.
                            3. If it is wrong, fix it and output the new answer inside <answer> tags."""

def call_model_chat_completions(prompt: str,
                                system: str = "give me only the final answer no explanation.",
                                model: str = MODEL,
                                temperature: float = 0.0,
                                timeout: int = 60,
                                max_tokens: int = 128,
                                message: list = []) -> dict:
    """
    Calls an OpenAI-style /v1/chat/completions endpoint and returns:
    { 'ok': bool, 'text': str or None, 'raw': dict or None, 'status': int, 'error': str or None, 'headers': dict }
    """
    url = f"{API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": model,
        "messages": message,
        "temperature": temperature,
        # "response_format":{"type":"text", "strict":False},#added this to force text output
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        status = resp.status_code
        hdrs   = dict(resp.headers)
        if status == 200:
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"ok": True, "text": text, "raw": data, "status": status, "error": None, "headers": hdrs}
        else:
            # try best-effort to surface error text
            err_text = None
            try:
                err_text = resp.json()
            except Exception:
                err_text = resp.text
            return {"ok": False, "text": None, "raw": None, "status": status, "error": str(err_text), "headers": hdrs}
    except requests.RequestException as e:
        return {"ok": False, "text": None, "raw": None, "status": -1, "error": str(e), "headers": {}}

def load_questions(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fp:
        data = json.load(fp)

    if not isinstance(data, list):
        raise ValueError("Input file must contain a list of question objects.")
    return data

#clearning up the models answer
def clean_ans(res):
   match = re.search(r'<answer>(.*?)</answer>', res, re.DOTALL | re.IGNORECASE)
   if match:
        return match.group(1).strip()
   return res #return response if  model forgot the tags
def google_search(query:str) -> str:
    print('model using google search tool ', query)
    try:
        with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5): #getting the top 5 reults
                    print('google search result ', r.get('body', 'result not found'))
                    return r.get('body', 'result not found')
    except Exception as e:
        return str(e)

#python tool 
def python_executioner(code):
    print('model using python tool ', code)
    output_buffer = io.StringIO()
    try:
        with redirect_stdout(output_buffer):
            exec(code, {})
        return output_buffer.getvalue()
    except Exception as e:
        return str(e)


def build_answers(questions: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    answers = []
    for idx, question in enumerate(questions, start=1):
        # Example: assume you have an agent loop that produces an answer string.
        # real_answer = agent_loop(question["input"])
        # answers.append({"output": real_answer})
        question = question['input']
        analogical_prompt = f""" {analogical_prompt_template}
        Main Question: {question}
        """
        # creting the payload 
        messages = [
            {"role": "system", "content": pre_analogical_sys_prompt},
            {"role": "user", "content": analogical_prompt}
        ]
        
        for _ in range(7):
            #allows for the model to use tools
            result = call_model_chat_completions(prompt=analogical_prompt, system=pre_analogical_sys_prompt, model=MODEL, temperature=0.0, timeout=60, max_tokens=2060  , message=messages) 
            model_ans = result['text'] or  "" #get the answer or return an empty string
            tool = re.search(r"(Google Search:|Python Executioner:)(.*)", model_ans)
            
            if tool:
                tool_name = tool.group(1).strip()
                tool_input = tool.group(2).strip()
                if tool_name == "Google Search:":
                    tool_output = google_search(tool_input)
                elif tool_name == "Python Executioner:":
                    tool_output = python_executioner(tool_input)
                #update the prompt with the tool output
                messages += [{"role": "system", "content": f"Tool Output: {tool_output}\n Continue with the main question."}]
            else:
                print("Model Answer with reasoning steps:", model_ans)
                break 
                
        
        #passing the modesl answer to the self refine prompt
        self_refine_prompt = f"""{self_refine_prompt_temp}
        Question: {question}
        Proposed Answer: {model_ans}
        Provide the final answer inside the <answer> tag. NO EXPlanation or fillers.
        """
        
        messages = [
            {"role": "system", "content": self_refine_sys_prompt},
            {"role": "user", "content": self_refine_prompt}
            ]
        
        
        result = call_model_chat_completions(prompt=self_refine_prompt, model=MODEL, temperature=0.0, max_tokens=2060 , timeout=60, message=messages)
        
        print("Model Answer:", clean_ans(result['text']))

        placeholder_answer = f"Placeholder answer for question {idx}"
        answers.append({"output": placeholder_answer})
    return answers


def validate_results(
    questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
) -> None:
    if len(questions) != len(answers):
        raise ValueError(
            f"Mismatched lengths: {len(questions)} questions vs {len(answers)} answers."
        )
    for idx, answer in enumerate(answers):
        if "output" not in answer:
            raise ValueError(f"Missing 'output' field for answer index {idx}.")
        if not isinstance(answer["output"], str):
            raise TypeError(
                f"Answer at index {idx} has non-string output: {type(answer['output'])}"
            )
        if len(answer["output"]) >= 5000:
            raise ValueError(
                f"Answer at index {idx} exceeds 5000 characters "
                f"({len(answer['output'])} chars). Please make sure your answer does not include any intermediate results."
            )


def main() -> None:
    questions = load_questions(INPUT_PATH)
    answers = build_answers(questions)

    with OUTPUT_PATH.open("w") as fp:
        json.dump(answers, fp, ensure_ascii=False, indent=2)

    with OUTPUT_PATH.open("r") as fp:
        saved_answers = json.load(fp)
    validate_results(questions, saved_answers)
    print(
        f"Wrote {len(answers)} answers to {OUTPUT_PATH} "
        "and validated format successfully."
    )


if __name__ == "__main__":
    main()

