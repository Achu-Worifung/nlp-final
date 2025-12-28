# NLP Final Project Agent

CSE 476 final project. The repo includes a tutorial notebook for experimentation and a CLI script to generate the required answers JSON for submission.


## Setup
- Python 3.9+ recommended.
- Install deps:
  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- Network access: the provided API host is only reachable on ASU network/VPN.

## Configuration
The code defaults to the provided classroom endpoint and model:
- `API_BASE="BASE-ADDRESS"`
- `MODEL="MODEL-NAME"`
- `API_KEY="API-KEY"`

## Generating answers for submission
Run the CLI to produce `cse_476_final_project_answers.json` in the required format:
```bash
python generate_answer_template.py
```
The script will:
- Load prompts from `cse_476_final_project_test_data.json`.
- Run the agent loop per question (analogical prompt, optional tools, self-refine grading pass).
- Write answers under the `output` field and validate length/format.

## Agent techniques implemented
- **Analogical self-prompting**: generate a similar example before solving the main question.
- **Tool calls**: detect `Google Search:` or `Python Executioner:` in the model output, run the tool, and feed results back.
- **Self-refine grading pass**: second call that audits and normalizes the final answer inside `<answer>` tags.
- **Few-shot prompting**: provided the model with example outputs for guidance.


## Key Implementation Details

### 1. Core API Call Function

**Function:** `call_model_chat_completions()`
- Handles all communication with the classroom LLM endpoint
- Accepts message arrays for multi-turn conversations
- Returns structured response dict with `ok`, `text`, `raw`, `status`, `error`, and `headers`
- Configurable temperature, max_tokens, and timeout parameters

**Function:** `google_search()`
- User DUckDuckGO API to return a web search, returns the 5 top results.
- Accepts a query as parameter
- Results are appended to the message and passed back to the Agent.

**Function:** `python_executioner()`
- Executes code in isolated namespace using `exec()` with stdout capture
- Takes code to be executed as parameter.
- Results are appended to the message and passed back to the Agent.

**Function:** `clean_ans()`
- Extract's model answers from its reasoning


### 2. Analogical Self-Prompting
**Prompt Template:** `analogical_prompt_template` and `pre_analogical_sys_prompt`
- System prompt instructs the model to think step-by-step with detailed explanations
- User prompt requests the model to generate a similar example question before solving the main problem
- Tools (Google Search, Python Executioner) are described in the prompt for optional use



### 3. Tool Integration (Google Search & Python Executioner)
**File:** `generate_answer_template.py` 

**Functions:** `google_search()` and `python_executioner()`
- **Google Search** : Uses DuckDuckGo API via `ddgs` library, returns top 5 results
- **Python Executioner** : Executes code in isolated namespace using `exec()` with stdout capture

**Tool Detection & Loop:** 
- Regex pattern `r"(Google Search:|Python Executioner:)(.*)"` detects tool invocations in model output
- Runs up to 7 iterations to allow multi-step tool usage
- Appends tool output back to message history to continue reasoning

### 4. Self-Refine Grading Pass

**Prompt Templates:** `self_refine_sys_prompt` and `self_refine_prompt_temp`
- Acts as an Auditor checking for logical flaws
- Enforces strict output formatting rules:
  - Boolean/Binary: outputs only "True" or "False"
  - Multiple choice: exact option text without labels
  - Math: LaTeX without `$` signs or units
  - Code: returns completed code solution
- Removes conversational filler phrases

**Answer Extraction:**  `clean_ans()` function extracts content between `<answer>` tags using regex.






