# Project rules (read first, in every task)
Project: green coffee bean machine learning + coffee globe website + a six-agent team (HumanLayer builds it, n8n runs it). This repo is a fork of the Ironhack Project 2 template.
## Folder map
Course files (extend, never rewrite without asking): README.md (still the course brief until we replace it), RUBRIC.md, requirements.txt, download_data.py, notebooks/, src/functions.py, data/README.md.
Ours: prompts/ agent prompts (source of truth) | n8n/ exported workflows | references/ source ledger | src/config.py seed and paths | globe/ the website, with globe/data/ for its data.
data/ and models/ contents are never committed.
Agents never see file paths. Code maps logical names to paths in src/config.py.
## 12-factor agents: always apply
When you write or change anything agent-related (prompts, n8n workflows, agent code), follow the 12 factors from github.com/humanlayer/12-factor-agents:
1 Agents output structured JSON next steps, not free prose.
2 Prompts are files in prompts/, versioned in git.
3 We build the context window ourselves (compact tagged events).
4 Tools are structured outputs that plain code executes.
5 One append-only event log is the single source of state.
6 Every agent can be launched, paused and resumed with a simple call.
7 Humans are contacted through tool calls at three gates: datasets, columns, publishing.
8 Control flow, budgets and hard rules live in code, never only in a prompt.
9 Errors enter the context as one short line; after 3 in a row, ask the human.
10 Keep agents small and focused.
11 Agents can be triggered from a webhook and notify by message.
12 Agents are stateless: new state = f(state, event).
Also: pre-fetch context in code instead of asking the model to fetch it. Cleaning and modelling are plain code, not LLM calls.
## Sources: always record them
Every source used anywhere in the project (data, paper, docs, tool, image, library) must have an entry in references/sources.json with: source_id, title, url, publisher_or_author, type, licence (as written, or "unknown"), licence_url, verification (opened_and_read | summary_only | search_result_only | access_blocked), used_for.
Never invent a URL, licence or number; "unknown" is fine. The website shows all of this behind a References button.
## Ironhack Project 2 rules (graded, see RUBRIC.md)
- Split once with a fixed random_state; the test set is used once; everything that learns from data lives inside a scikit-learn Pipeline.
- Reusable logic lives in src/functions.py; the seed and the paths are defined once in src/config.py.
- Never commit the contents of data/ or models/. This repo is a fork of a public repo, so never commit keys, tokens or .env files.
- Small, frequent commits with clear messages, on branches. Notebooks must run top to bottom on a fresh kernel.
- Check finished work against RUBRIC.md.
## Working style
The person is a beginner and must be able to explain every line. Use only techniques covered in the Ironhack lessons, keep code simple, and add short comments saying why.
