# Requirement: Agent Skill Onboarding And Callability Guide

- **Date**: 2026-04-09
- **Grade**: M (documentation)
- **Status**: frozen

## Goal

Provide a project-native guidance document that tells an AI or agent how to add a new skill into Vibe-Skills and ensure the skill can be routed and called correctly.

## Deliverable

A Chinese-language Markdown guide under `docs/install/` that covers:

1. Skill intake and classification
2. Mirroring skill assets into the repository
3. Canonical vs custom routing admission
4. Complex skill handling (`skills/`, `commands/`, `hooks/`, `agents/`)
5. Verification steps proving the skill is callable

## Constraints

- Follow the repository's existing governed routing model
- Do not describe directory copy as sufficient for callability
- Keep the guide aligned with current config files and CLI verification surfaces
- Prefer operational steps over abstract explanation

## Acceptance Criteria

- [ ] The guide explains the minimum conditions for "已接入可调用"
- [ ] The guide explains how to add canonical routing entries
- [ ] The guide explains how to verify route selection and runtime health
- [ ] The guide explains how complex multi-surface skills should be modeled
- [ ] The guide is discoverable from `docs/install/README.md`
