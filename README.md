# SAIL: Software Architecture Iconographic Language

**SAIL (Software Architecture Iconographic Language)** is an architecture description language designed to make system boundaries, interfaces, behaviors, constraints, and validation rules explicit for both human engineering teams and AI-assisted development workflows.

## 🛑 The Core Problem: Why SAIL?

Software architecture often fails because it devolves into "shelfware"—vague diagrams or tribal knowledge trapped in a single person's head.

Today, this problem is compounded by AI. AI coding agents are incredibly fast, but without strict architectural context, they guess. They cross system boundaries, break interface contracts, and violate constraints that human architects take for granted.

SAIL was created to bridge this gap. It provides a framework that is visually clear for humans to understand, yet structured and explicit enough for AI agents to follow without hallucinating or introducing architectural drift.

## 🏗️ Repository Contents

This repository serves as a reference implementation and open-source companion to the SAIL framework. It provides the templates, schemas, and AI prompts necessary to implement SAIL in your own engineering workflows.

### 1. Architectural Schemas (`/schemas`)

Provides structured templates (JSON/YAML) for defining the five pillars of the SAIL framework:

* **Boundaries:** Explicitly defining system and domain boundaries.
* **Interfaces:** API and contract definitions.
* **Behaviors:** Expected state changes and event flows.
* **Constraints:** Hard limitations (performance, security, deployment) that cannot be violated.
* **Validation Rules:** Criteria for assessing whether the architecture has been successfully met.



### 2. AI Generator-Verifier Workflows (`/ai-prompts`)

Contains system context blocks and prompt structures designed to feed SAIL constraints directly into AI coding agents (like GitHub Copilot, Claude, or ChatGPT).

* **Generator Prompts:** Context wrappers to ensure generated code strictly adheres to defined interfaces and constraints.
* **Verifier Prompts:** Logic for AI-assisted drift detection and architecture conformance checking.


### 3. SAIL-Compliant ADRs (`/adrs`)

Templates for integrating SAIL concepts into standard Architecture Decision Records (ADRs). These templates ensure that every technical decision captures its impact on existing boundaries, behaviors, and constraints.

## 📖 The Book: Mastering the SAIL Framework
This repository is the practical companion to the book ***Applied Software Architecture: Mastering the SAIL Framework*** (published June 2026).

To fully understand the theory, iconographic design, and executive strategy behind the framework, you can find the official publication below:
*   🛒 **[Purchase on Amazon (ISBN: 9798181660588)](https://www.amazon.com/dp/B0H5QKVND6)** 
*   🔗 **[Official Framework Site](https://getsail.org/book)**

## 👨‍💻 About the Creator

**Jim Simmermon** is a Principal System Architect and hands-on engineering leader based in the Netherlands with over 30 years of experience. He specializes in distributed systems, cloud modernization, and bridging the gap between executive technology strategy and production-level execution.

* [LinkedIn Profile](https://www.linkedin.com/in/simmermon)
* [Email: jim@thesimmermon.com](mailto%3Ajim%40thesimmermon.com)

---

*Note: This repository contains reference templates and structural guides. For full implementation details, refer to the published book.*
