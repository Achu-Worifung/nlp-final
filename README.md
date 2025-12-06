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
- `API_BASE="http://10.4.58.53:41701/v1"`
- `MODEL="bens_model"`
- `API_KEY="cse476"`

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
**File:** `generate_answer_template.py` (lines 68-101) and `final_project_tutorial.ipynb` (cell 2)

**Function:** `call_model_chat_completions()`
- Handles all communication with the classroom LLM endpoint
- Accepts message arrays for multi-turn conversations
- Returns structured response dict with `ok`, `text`, `raw`, `status`, `error`, and `headers`
- Configurable temperature, max_tokens, and timeout parameters

### 2. Analogical Self-Prompting
**File:** `generate_answer_template.py` (lines 28-40, 169-174)

**Prompt Template:** `analogical_prompt_template` and `pre_analogical_sys_prompt`
- System prompt instructs the model to think step-by-step with detailed explanations
- User prompt requests the model to generate a similar example question before solving the main problem
- Tools (Google Search, Python Executioner) are described in the prompt for optional use

**Implementation:** Lines 169-174 construct the initial message payload combining system and user prompts.

### 3. Tool Integration (Google Search & Python Executioner)
**File:** `generate_answer_template.py` (lines 130-155)

**Functions:** `google_search()` and `python_executioner()`
- **Google Search** (lines 130-139): Uses DuckDuckGo API via `ddgs` library, returns top 5 results
- **Python Executioner** (lines 141-150): Executes code in isolated namespace using `exec()` with stdout capture

**Tool Detection & Loop:** Lines 176-190 in `build_answers()`
- Regex pattern `r"(Google Search:|Python Executioner:)(.*)"` detects tool invocations in model output
- Runs up to 7 iterations to allow multi-step tool usage
- Appends tool output back to message history to continue reasoning

### 4. Self-Refine Grading Pass
**File:** `generate_answer_template.py` (lines 42-64, 193-210)

**Prompt Templates:** `self_refine_sys_prompt` and `self_refine_prompt_temp`
- Acts as an Auditor checking for logical flaws
- Enforces strict output formatting rules:
  - Boolean/Binary: outputs only "True" or "False"
  - Multiple choice: exact option text without labels
  - Math: LaTeX without `$` signs or units
  - Code: returns completed code solution
- Removes conversational filler phrases

**Answer Extraction:** Lines 122-128 `clean_ans()` function extracts content between `<answer>` tags using regex.






