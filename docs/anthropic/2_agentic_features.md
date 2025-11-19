# 2. Agentic Features of the Claude API

This document provides a deep dive into the agentic capabilities of the Claude API, focusing on how to build and manage AI agents.

## Building Agentic Systems with Claude

The Claude API is designed to support the creation of sophisticated AI agents that can perform complex tasks, interact with external tools, and maintain context over long periods. The key to building agentic systems with Claude is to leverage its tool-using capabilities and the new features introduced with Sonnet 4.5.

## Key Agentic Features

### 1. Tool Use (Function Calling)

Tool use, also known as function calling, allows Claude to interact with external tools and APIs to perform tasks, manipulate data, and provide dynamic and accurate responses. Instead of directly executing code, Claude generates structured calls (e.g., JSON schema) for predefined tools, which your application then executes.

**How it Works:**

1.  **User Request with Tools**: You send a user's query to the Claude API, along with a list of available tools.
2.  **Claude Identifies Tool Need**: Claude processes the query and tool descriptions. If it determines that a tool can help fulfill the request, its response indicates which tool it wants to use and the necessary input parameters.
3.  **Application Executes Tool**: Your application receives Claude's response, parses the tool name and parameters, and then executes the corresponding function or API call in your environment.
4.  **Subsequent Request with Tool Result**: The result from the tool's execution is sent back to Claude in a new API call.
5.  **Claude's Final Response**: Claude uses the tool's output to formulate a comprehensive and accurate final response to the user's initial query.

### 2. Planning and Reasoning

Claude's advanced reasoning capabilities enable it to understand complex inputs and engage in multi-step planning. Developers can design prompts that guide Claude to break down complex tasks into smaller, manageable steps, allowing it to process each consideration with a separate LLM call for better performance.

### 3. Memory

To maintain context and perform multi-turn interactions, agents require memory. Claude can store and consult information from dedicated memory files. The Claude Agent SDK includes features for context management, such as automatic compaction of previous messages when token limits are approached, ensuring the agent doesn't "forget" important details over long conversations.

### 4. Self-Correction and Reflection

A key aspect of agentic behavior is the ability to evaluate and improve one's own work. Agents built with Claude can be designed to check their output and self-correct. This is achieved by providing Claude with clear rules or code-based validation mechanisms to assess its progress and identify errors.

### 5. Code Execution

Claude can directly run Python code within a sandboxed environment during API calls. This capability is particularly powerful for tasks like data analysis, generating visualizations, and iterating on code.

### 6. Subagents and Parallelization

The Claude Agent SDK supports the creation of subagents. These specialized agents can work on different tasks simultaneously, enabling parallelization of complex workflows.

## The Claude Agent SDK

To simplify the process of building agents, Anthropic provides the Claude Agent SDK. This SDK offers a set of foundational components for building production-ready agents, including:

*   **Context Management**: Tools for managing the context of a conversation.
*   **Tool Ecosystem**: A comprehensive set of pre-built tools, including file operations, code execution, web search, and an MCP extensibility.
*   **Advanced Permissions**: Features for controlling what an agent is allowed to do.
*   **Production Essentials**: Components for error handling, session management, and other production needs.

## Further Reading

For more detailed information on building agentic systems with Claude, please refer to the official Anthropic documentation.