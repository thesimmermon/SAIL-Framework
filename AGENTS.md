# Repository Guidelines

## Project Structure & Module Organization

This repository publishes the SAIL framework specification, schemas, examples, and validation utilities. Core machine-readable definitions live in `schema/`, including the architecture and codebook JSON schemas. Contributor-facing prompt templates live in `templates/`. Public site content, rendered specification pages, images, downloads, and sample architectures live under `docs/`; reusable visual assets are primarily in `docs/specification/images/`. Validator and context-building scripts live in `tools/`.

## Website Guidance

This repository contains `getsail.org`, the official website for SAIL (Software Architecture Iconographic Language). When modifying the site, preserve SAIL terminology and semantics, and do not invent SAIL capabilities or adoption claims. Maintain the distinction between visual diagrams and the machine-readable model. SAIL is not an "AI architecture language"; it is a software architecture language whose explicit semantics also make it useful as context for AI coding agents. Reuse existing site styles and components where sensible, maintain responsive design and accessibility, do not break existing URLs, and run the project's build/test/lint workflow before considering work complete.

## Build, Test, and Development Commands

- `cd tools; npm install`: install the Node validator dependency (`ajv`).
- `cd tools; npm run validate -- ..\docs\examples\GridGuard\GridGuard.sail`: validate a `.sail` file against the JSON schema with Node.
- `python tools\validate_sail.py docs\examples\GridGuard\GridGuard.sail`: run the Python schema validator. Install `jsonschema` first if needed.
- `python tools\semantic-check-sail.py docs\examples\GridGuard\GridGuard.sail`: run semantic checks that go beyond file shape.
- `python tools\build-ai-context.py <input.sail>`: build an AI-oriented context artifact when updating agent workflows.

## Coding Style & Naming Conventions

Use UTF-8 text files and keep JSON schemas formatted with two-space indentation. Python tools use four-space indentation, type hints where useful, `pathlib.Path`, and clear CLI exit codes. Node tools are ES modules (`.mjs`) with two-space indentation and descriptive camelCase variables. Keep script names action-oriented, for example `validate_sail.py`, `semantic-check-sail.py`, and `build-ai-context.py`. Template files should retain their numeric ordering prefix, such as `01-agent-architecture-context.md`.

## Testing Guidelines

There is no separate unit-test suite yet; validation commands are the primary regression checks. For schema, validator, or example changes, run both schema validation and semantic checks against at least one known sample such as `docs\examples\GridGuard\GridGuard.sail`. Add or update focused `.sail` fixtures when changing validation behavior, and document expected failures in the relevant README or schema notes.

## Commit & Pull Request Guidelines

Recent history uses short, imperative summaries such as `element sizing` and `fixed icon sizes`; follow that concise style unless a scoped prefix adds clarity. Pull requests should explain the affected area, list validation commands run, link related issues or docs changes, and include screenshots for visible `docs/` or stylesheet updates. Avoid mixing schema, tooling, and site presentation changes unless they are part of the same feature.

## Security & Configuration Tips

Do not commit generated archives, credentials, or local dependency folders. Treat downloadable binaries under `docs/downloads/` as intentional release artifacts and call out any replacement or size change in the pull request.
