# Vapi MCP Documentation

This document provides a summary of Vapi's implementation of the Model Context Protocol (MCP).

## Overview

Vapi utilizes the Model Context Protocol (MCP) to enable its voice AI agents to interact with external tools and APIs. MCP is an open standard that standardizes how applications expose tools and context to large language models (LLMs).

## Key Concepts

*   **MCP Server**: A server that exposes a collection of tools that can be called by an MCP client (such as a Vapi voice agent).
*   **MCP Tool**: A specific function hosted on an MCP server, such as `create_assistant` or `make_phone_call`.
*   **Server-Sent Events (SSE)**: MCP servers often use SSE for real-time, unidirectional communication from the server to clients. This is used for streaming metrics, logs, status updates, and partial responses.

## Vapi's Implementation

Vapi's voice AI agents act as MCP clients, allowing them to connect to MCP servers and execute tools. This enables a wide range of integrations and allows agents to perform complex workflows.

## Further Reading

For more detailed information, please refer to the official Vapi documentation, which includes sections on MCP SDKs.
