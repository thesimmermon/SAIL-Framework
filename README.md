# SAIL: Software Architecture Iconographic Language

**SAIL (Software Architecture Iconographic Language)** is an architecture description language designed to make system boundaries, interfaces, behaviors, constraints, and validation rules explicit for both human engineering teams and AI-assisted development workflows[cite: 3, 7, 8].

## 🛑 The Core Problem: Why SAIL?

Software architecture often fails because it devolves into "shelfware"—vague diagrams or tribal knowledge trapped in a single person's head[cite: 8].

Today, this problem is compounded by AI. AI coding agents are incredibly fast, but without strict architectural context, they guess. They cross system boundaries, break interface contracts, and violate constraints that human architects take for granted[cite: 4].

SAIL was created to bridge this gap. It provides a framework that is visually clear for humans to understand, yet structured and explicit enough for AI agents to follow without hallucinating or introducing architectural drift[cite: 4, 8].

## 🏗️ Repository Contents

This repository serves as a reference implementation and open-source companion to the SAIL framework. It provides the templates, schemas, and AI prompts necessary to implement SAIL in your own engineering workflows.

### 1. Architectural Schemas (`/schemas`)

Provides structured templates (JSON/YAML) for defining the five pillars of the SAIL framework:

* **Boundaries:** Explicitly defining system and domain boundaries[cite: 3].
* **Interfaces:** API and contract definitions[cite: 3].
* **Behaviors:** Expected state changes and event flows[cite: 3].
* **Constraints:** Hard limitations (performance, security, deployment) that cannot be violated[cite: 3].
* **Validation Rules:** Criteria for assessing whether the architecture has been successfully met[cite: 3].

> *[Insert a brief 5-10 line JSON or YAML snippet here showing a basic SAIL component definition]*

### 2. AI Generator-Verifier Workflows (`/ai-prompts`)

Contains system context blocks and prompt structures designed to feed SAIL constraints directly into AI coding agents (like GitHub Copilot, Claude, or ChatGPT).

* **Generator Prompts:** Context wrappers to ensure generated code strictly adheres to defined interfaces and constraints[cite: 3].
* **Verifier Prompts:** Logic for AI-assisted drift detection and architecture conformance checking[cite: 3, 7].

> *[Insert a brief example of a system prompt, e.g., "You are an AI assistant bound by the following SAIL constraints..."]*

### 3. SAIL-Compliant ADRs (`/adrs`)

Templates for integrating SAIL concepts into standard Architecture Decision Records (ADRs)[cite: 3, 7]. These templates ensure that every technical decision captures its impact on existing boundaries, behaviors, and constraints.

## 📖 The Book: Mastering the SAIL Framework
This repository is the practical companion to the book ***Applied Software Architecture: Mastering the SAIL Framework*** (published June 2026).

To fully understand the theory, iconographic design, and executive strategy behind the framework, you can find the official publication below:
*   🛒 **[Purchase on Amazon (ISBN: 9798181660588)](https://www.amazon.com/dp/B0D5S1L5X3)** *(Note: Replace with the exact short-link to your book)*
*   🔗 **[Official Framework Site](https://getsail.org/book)**

## 👨‍💻 About the Creator

**Jim Simmermon** is a Principal System Architect and hands-on engineering leader based in the Netherlands with over 30 years of experience[cite: 3, 8]. He specializes in distributed systems, cloud modernization, and bridging the gap between executive technology strategy and production-level execution[cite: 8].

* [LinkedIn Profile](https://www.google.com/search?q=https://www.linkedin.com/in/simmermon)[cite: 8]
* [Email: jim.simmermon@outlook.com](https://www.google.com/search?q=mailto%3Ajim.simmermon%40outlook.com)[cite: 4, 8]

---

*Note: This repository contains reference templates and structural guides. For full implementation details, refer to the published book.*
