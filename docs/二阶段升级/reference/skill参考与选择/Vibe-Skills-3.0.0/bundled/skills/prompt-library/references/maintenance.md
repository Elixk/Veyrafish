# Prompt Library Maintenance

## Rules

1. Do not dump large external prompt collections here unchanged.
2. Keep prompts short enough to be reusable and reviewable.
3. Prefer one prompt per file.
4. Update `index.json` whenever you add, remove, or rename a prompt.
5. If a prompt becomes a workflow rather than an asset, consider promoting it into a standalone skill.

## Recommended Metadata

Each prompt file should document:

- `id`
- `title`
- `category`
- `tags`
- `use_when`
- `inputs`
- `output_expectation`

## Validation Checklist

- File is placed in the correct category
- Metadata is complete
- `index.json` entry exists
- Prompt purpose is distinct from existing prompts
