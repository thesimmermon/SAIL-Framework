remove the citation marks from this text:

# SAIL: Software Architecture Iconographic Language

[![Book: Applied Software Architecture](https://img.shields.io/badge/Book-Applied_Software_Architecture-blue.svg)](https://getsail.org/book)
[![Creator: Jim Simmermon](https://img.shields.io/badge/Creator-Jim_Simmermon-orange.svg)](https://www.linkedin.com/in/simmermon)

**SAIL (Software Architecture Iconographic Language)** is an architecture description language designed to make system boundaries, interfaces, behaviors, constraints, and validation rules explicit for both human engineering teams and AI-assisted development workflows.

## 🛑 The Core Problem: Why SAIL?
Software architecture often fails because it devolves into "shelfware"—vague diagrams or tribal knowledge trapped in a single person's head. Today, this problem is compounded by AI. AI coding agents are incredibly fast, but without strict architectural context, they guess and introduce architectural drift. 

SAIL was created to bridge this gap. It provides a framework that is visually clear for humans to understand, yet structured and explicit enough for AI agents to follow without hallucinating.

## 🏗️ Repository Contents
This repository contains the official SAIL specification, validation tools, and AI guardrail templates[cite: 9].

### 1. The Xebec Designer
This repository includes the Xebec designer, the visual and iconographic modeling tool used to construct and map SAIL architectures for human comprehension before they are parsed into machine-readable formats.

### 2. Core Schemas (`/schema`)
The foundational JSON schemas defining the SAIL framework[cite: 9]:
*   `sail.schema.json`[cite: 9]: The primary schema defining boundaries, interfaces, behaviors, and constraints.
*   `sail-codebook.schema.json` & `sail-codebook.json`[cite: 9]: The standardized data dictionaries for SAIL implementation.
*   See `SCHEMA-NOTES.md`[cite: 9] in the root directory for implementation details.

### 3. AI Agent Templates (`/templates`)
Markdown templates designed to enforce SAIL guardrails within LLM/AI workflows[cite: 9]:
*   `01-agent-architecture-context.md`[cite: 9]: Establishes system boundaries for the AI.
*   `02-implement-feature-with-sail-guardrails.md`[cite: 9]: Prompts for feature generation without violating constraints.
*   `03-review-code-against-sail.md`[cite: 9]: AI instructions for architectural drift detection.
*   `04-propose-architecture-change.md`[cite: 9]: Structured format for architectural mutation.

### 4. Validation Tools (`/tools`)
Python scripts used to parse, validate, and build context windows for AI agents[cite: 9]:
*   `validate-sail.py`[cite: 9]: Script to validate your architecture against the SAIL schema.
*   `build-ai-context.py`[cite: 9]: Compiles SAIL definitions into an optimized context window for LLMs.

### 5. Reference Examples (`/examples`)
Real-world outputs and summaries[cite: 9]:
*   `GridGuard.ai-context.summary.json`[cite: 9]
*   `model-diff.example.json`[cite: 9]
*   `validation-report.example.json`[cite: 9] (See `VALIDATION-RESULTS.json`[cite: 9] at root for live output).

## 📖 The Book: Mastering the SAIL Framework
This repository is the practical companion to the book ***Applied Software Architecture: Mastering the SAIL Framework*** (published June 2026).

To fully understand the theory, iconographic design, and executive strategy behind the framework, you can find the official publication below:
*   🛒 **[Purchase on Amazon (ISBN: 9798181660588)](https://www.amazon.com/dp/B0H5QKVND6)** 
*   🔗 **[Official Framework Site](https://getsail.org/book)**

## 👨‍💻 About the Creator

**Jim Simmermon** is a Principal System Architect and hands-on engineering leader based in the Netherlands with over 30 years of experience. He specializes in distributed systems, cloud modernization, and bridging the gap between executive technology strategy and production-level execution.

* [LinkedIn Profile](https://www.linkedin.com/in/simmermon)
* [Email: jim@thesimmermon.com](mailto:jim@thesimmermon.com)

---

*Note: This repository contains reference templates and structural guides. For full implementation details, refer to the published book.*
