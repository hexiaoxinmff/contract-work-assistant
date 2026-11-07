# Contract Work Assistant

A platform-independent skill for AI agents that supports three contract-document tasks:

- Text and DOCX formatting checks.
- Cross-checking contract content against the document and materials supplied by the user.
- Filling an existing DOCX template with explicitly supplied facts and saving a separate output.

The skill includes three standard-library Python helpers under `contract-work-assistant/tools/`:

- `inspect_docx_format.py` reads DOCX run properties, paragraph styles, style inheritance and document defaults.
- `fill_docx.py` performs unique, exact text replacements in a new output file and refuses ambiguous replacements or overwriting the source.
- `compare_docx.py` compares text changes and package structure between a source document and its output.

The scripts do not provide legal opinions, determine enforceability, or submit documents to business systems. File operations require the host environment to provide Python/command execution. The skill can be adapted to any agent platform that supports skills or equivalent instruction packages; actual file-tool availability depends on the host. Use only documents that you are authorized to process, and have a responsible person review all outputs.

## Install

Import or copy the complete `contract-work-assistant` folder into the skills location supported by your AI agent. Keep `SKILL.md`, `tools/`, and `references/` together. Follow the host platform's skill installation steps, then start a new conversation and confirm the loaded version before use.

See [`references/使用与后期更新.md`](contract-work-assistant/references/使用与后期更新.md) for task examples, tool behavior, installation and upgrade guidance.
