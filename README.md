# Contract Work Assistant

A platform-independent v2.2 trial skill for AI agents that supports contract-document tasks. Users can provide their own current template at use time; templates are not stored in this public package:

- Context-aware proofreading and DOCX formatting checks, with task-appropriate review gates.
- Comparing service contracts and prices using the supplied terms, units, scope and tax information.
- Cross-checking contract content across contracts and supporting documents supplied by the user, with explicit file-readability and version limits.
- Filling an existing DOCX template with explicitly supplied facts and saving a separate output.
- Turning everyday-language requests into usable task prompts or carrying out the task directly when that is what the user asks.

The skill includes seven standard-library Python helpers under `contract-work-assistant/tools/`:

- `check_environment.py` checks first-use runtime and file access prerequisites. `inspect_docx_format.py` reads DOCX run properties, paragraph styles, style inheritance and document defaults.
- `find_docx_occurrences.py` locates matching text and context in DOCX body paragraphs for review before edits.
- `fill_docx.py` performs unique, exact text replacements in a new output file and refuses ambiguous replacements or overwriting the source.
- `compare_docx.py` compares text changes and package structure between a source document and its output.
- `compare_service_text.py` locates text-sequence differences and exact-title correspondence candidates in two TXT or DOCX files; it is not a semantic or legal review.
- `compare_price_inputs.py` reads explicitly extracted quote data from standard input and calculates annualized monthly/yearly rates and limited per-visit/per-area amounts; it does not extract data from contracts or establish comparability.

The included scripts cover DOCX, TXT, structured quote calculations and environment checks; they do not provide PDF OCR or legacy DOC parsing. The scripts do not provide legal opinions, determine enforceability, or submit documents to business systems. File operations require the host environment to provide Python/command execution. The skill can be adapted to any agent platform that supports skills or equivalent instruction packages; actual file-tool availability depends on the host. Use only documents that you are authorized to process, and have a responsible person review all outputs.

## Install

Import or copy the complete `contract-work-assistant` folder into the skills location supported by your AI agent. Keep `SKILL.md`, `tools/`, and `references/` together. Follow the host platform's skill installation steps, then start a new conversation and confirm the loaded version before use.

See [`prompt-library.md`](contract-work-assistant/references/prompt-library.md) for everyday-language examples and prompt patterns, [`验收案例.md`](contract-work-assistant/references/验收案例.md) for fictional acceptance scenarios, and [`使用与后期更新.md`](contract-work-assistant/references/使用与后期更新.md) for installation and upgrade guidance.





