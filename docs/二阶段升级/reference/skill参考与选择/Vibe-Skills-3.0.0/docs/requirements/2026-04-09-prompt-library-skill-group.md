# Requirement: Prompt Library Skill Group

- **Date**: 2026-04-09
- **Grade**: L (governed documentation + runtime surface extension)
- **Status**: frozen

## Goal

Add a first-party `prompt-library` skill group so user-owned prompts of different types can be stored, organized, retrieved, and reused inside Vibe-Skills without creating a second router or mirroring an external prompt marketplace.

## Deliverable

1. A new `bundled/skills/prompt-library/` skill group with:
   - `SKILL.md`
   - categorized `prompts/` directories
   - `index.json`
   - `references/` guidance
2. Canonical routing admission for `prompt-library`
3. Documentation updates explaining where local prompts belong and how AI/Agent should maintain them

## Constraints

- Keep canonical router as the only route authority
- Model `prompt-library` as a local prompt asset surface, not an external prompt marketplace clone
- Avoid conflicting with the existing `prompt-lookup` skill, which remains the external prompt retrieval/improvement surface
- Keep the structure extensible so future user prompts can be added without changing the routing model

## Acceptance Criteria

- [ ] `bundled/skills/prompt-library/` exists with a usable scaffold
- [ ] `prompt-library` is admitted into canonical routing
- [ ] Routing rules distinguish local prompt assets from external prompt retrieval
- [ ] Management docs explain how to add prompts into the new skill group
- [ ] Basic route and doc checks pass
