# Prompt Library

`prompt-library` is the local prompt asset surface for repository-owned prompts.

## Purpose

Use this directory when you want to keep many prompts of different types inside Vibe-Skills without turning every prompt into a separate skill.

## Layout

```text
prompt-library/
├── SKILL.md
├── index.json
├── prompts/
│   ├── coding/
│   ├── research/
│   ├── writing/
│   ├── review/
│   ├── translation/
│   ├── agent-control/
│   └── business/
└── references/
```

## How to Add a Prompt

1. Pick the correct category folder under `prompts/`.
2. Copy `_template.md` in that category and rename it.
3. Fill in the metadata and prompt body.
4. Register the prompt in `index.json`.
5. Run routing and doc verification if the change affects prompt-library behavior.

## Boundary

- Use `prompt-library` for local prompt assets stored in this repository.
- Use `prompt-lookup` for external prompt discovery and prompts.chat integration.
