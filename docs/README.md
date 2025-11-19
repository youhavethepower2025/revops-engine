# FORGE Documentation Protocol

**Objective:** To create a standardized documentation system optimized for AI Agent consumption. This protocol ensures that all documentation is structured, comprehensive, and machine-readable, enabling agents to effectively understand and utilize the available tools, APIs, and systems.

**Core Principle:** Document for clarity, precision, and actionability. Assume the primary consumer of this documentation is an AI agent, not a human. Human readability is a secondary benefit.

---

## Documentation Structure

All new documentation for a service, API, or tool should follow this hierarchical structure, inspired by the `anthropic` documentation. Each section should be a separate Markdown file, numbered for sequential understanding.

### 1. `1_introduction.md`

*   **Purpose:** High-level overview of the service/tool.
*   **Content:**
    *   **`## Overview`**: What is this service? What is its primary function?
    *   **`## Key Architectural Concepts`**: Explain the core design principles and architecture. Use diagrams (MermaidJS is preferred for its text-based nature) and bullet points.
    *   **`## Core Features`**: List the main capabilities in a clear, concise manner.
    *   **`## Use Cases`**: Provide concrete examples of what this service can be used for.

### 2. `2_functional_breakdown.md`

*   **Purpose:** A detailed breakdown of the service's functions and capabilities. This section should be highly detailed and specific.
*   **Content:**
    *   **`## Feature Deep Dive`**: For each feature listed in the introduction, provide a detailed explanation.
    *   **`## How it Works`**: Step-by-step explanations of key workflows. Use numbered lists and code snippets.
    *   **`## Data Flow`**: Describe how data moves through the system. Use diagrams and clear descriptions of data structures.

### 3. `3_integration_guide.md`

*   **Purpose:** Practical instructions for integrating with the service.
*   **Content:**
    *   **`## Authentication`**: Detailed instructions on how to authenticate with the API. Include examples for different authentication methods (e.g., API keys, OAuth).
    *   **`## Quick Start`**: A step-by-step guide to making a first successful API call. Include a complete, runnable code example.
    *   **`## Core Workflows`**: Detailed examples for the most common use cases.
    *   **`## Error Handling`**: A list of common error codes and how to handle them.

### 4. `4_api_reference.md`

*   **Purpose:** A comprehensive, machine-readable reference for the API.
*   **Content:**
    *   **`## Endpoints`**: A list of all API endpoints.
    *   **`## Data Structures`**: Detailed descriptions of all data structures used in the API, preferably with JSON schema examples.
    *   **For each endpoint, provide:**
        *   **`### [HTTP_METHOD] [ENDPOINT_PATH]`**: e.g., `### POST /v1/users`
        *   **`#### Description`**: A clear description of what the endpoint does.
        *   **`#### Parameters`**: A table listing all request parameters, their types, whether they are required, and a description.
        *   **`#### Request Body`**: An example of the request body in JSON format.
        *   **`#### Response`**: An example of a successful response body in JSON format.
        *   **`#### Error Responses`**: Examples of error responses in JSON format.

---

## Best Practices for Agent-Readable Documentation

*   **Be Explicit:** Avoid ambiguity. State facts and instructions directly.
*   **Use Structured Data:** Whenever possible, use structured formats like JSON, YAML, or tables within your Markdown.
*   **Provide Complete Examples:** Code examples should be complete, runnable, and well-commented (for the agent's understanding, not a human's).
*   **Keep it Updated:** Documentation must be kept in sync with the code. Stale documentation is worse than no documentation.
*   **Cross-Reference:** Link between related sections of the documentation to provide a complete picture.

This protocol is not a suggestion; it is the standard for all documentation in this project. Adherence is mandatory.
