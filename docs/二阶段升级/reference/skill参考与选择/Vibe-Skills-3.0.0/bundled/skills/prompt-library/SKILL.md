---
name: prompt-library
description: |
  Activates when the user wants to manage, browse, classify, add, or reuse local prompt assets inside this repository.
  Use for local prompt libraries, internal prompt catalogs, prompt taxonomy, prompt packs, prompt maintenance, and selecting a prompt from bundled assets.
  Prefer this skill for local prompt asset workflows; prefer `prompt-lookup` for external prompt retrieval or prompts.chat.
---

# Prompt Library

Use this skill for the repository's local prompt asset surface.

This skill does not replace the router and does not create a second prompt marketplace.
It is the bounded local prompt-library lane for user-owned prompt assets that live in this repo.

## When To Use

Use this skill when the user asks to:

- create a local prompt library
- add prompts into this repository
- classify prompts by category or task
- maintain a prompt catalog or index
- retrieve a prompt from bundled local assets
- standardize prompt file structure and metadata
- keep prompt assets organized for later AI/Agent reuse

Do not use this skill for:

- searching external prompt marketplaces
- retrieving prompts from prompts.chat
- generic prompt improvement when no local asset management is involved

Use `prompt-lookup` instead for those external retrieval and prompt-improvement tasks.

## Local Asset Contract

The canonical local asset surfaces for this skill are:

- `index.json`
- `prompts/`
- `references/taxonomy.md`
- `references/maintenance.md`

Prompt files should be organized by category under `prompts/`.

## Working Rules

1. Prefer adding prompts to the correct category folder instead of creating flat prompt dumps.
2. Keep prompt metadata aligned with `index.json`.
3. Treat local prompt assets as repository-owned material, not as an external prompt mirror.
4. When a prompt belongs to an execution workflow rather than a reusable asset library, consider a dedicated skill instead of storing it here.

