# 3. Claude Skills

This document provides a detailed explanation of the new "skills" feature in the Claude API.

## What are Skills?

Skills are modular, reusable task components that extend Claude's capabilities with specialized expertise. They allow you to encapsulate complex logic and workflows into a single, callable unit that can be used by an AI agent. This is a powerful feature for building complex, agentic systems.

## Key Features of Skills

*   **Modularity**: Skills are self-contained units of functionality that can be developed, tested, and deployed independently.
*   **Reusability**: Skills can be reused across multiple agents and applications.
*   **Composability**: Skills can be combined to create more complex workflows.
*   **Portability**: Skills can be easily shared and used in different environments.
*   **Executable Code**: Skills can include executable code, allowing them to perform a wide range of tasks.

## Creating and Using Skills

Skills are typically structured as folders containing a `SKILL.md` file and optional scripts or templates. The `SKILL.md` file contains instructions and metadata for the skill, while the scripts and templates provide the implementation.

### The `SKILL.md` File

The `SKILL.md` file is the entry point for a skill. It contains the following information:

*   **Name**: The name of the skill.
*   **Description**: A description of what the skill does.
*   **Inputs**: The inputs that the skill accepts.
*   **Outputs**: The outputs that the skill produces.
*   **Instructions**: The instructions for how to use the skill.

### Example: A Simple "Hello World" Skill

Here is an example of a simple "Hello World" skill:

**`SKILL.md`**
```markdown
# Hello World

**Description:** A simple skill that returns a "Hello, World!" message.

**Inputs:** None

**Outputs:**

*   `message`: A string containing the "Hello, World!" message.

**Instructions:**

1.  Call the skill.
2.  The skill will return a "Hello, World!" message.
```

### Dynamic Invocation

Claude can automatically identify and invoke relevant skills based on a user's request. This is done by providing Claude with a list of available skills and their descriptions. Claude will then use its reasoning capabilities to determine which skill to use for a given task.

## Pre-built and Custom Skills

Anthropic provides a set of pre-built skills for common tasks, such as creating and editing PowerPoint, Excel, Word, and PDF documents. Developers can also create their own custom skills to perform specialized tasks.

## Further Reading

For more detailed information on creating and using skills, please refer to the official Anthropic documentation.