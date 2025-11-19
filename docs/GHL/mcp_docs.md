# GoHighLevel (GHL) MCP Documentation

This document provides a summary of the GoHighLevel (GHL) Model Context Protocol (MCP) server.

## Overview

The GoHighLevel MCP server is a standardized, secure protocol designed to enable AI agents to read and write data within the GoHighLevel platform without requiring traditional SDKs or complex custom integrations. It acts as a bridge, allowing AI models to connect with various GoHighLevel data sources and tools through a unified HTTP protocol.

## Key Concepts

*   **MCP Server**: A secure HTTP endpoint that exposes a collection of tools that can be called by an MCP client (such as a voice AI agent).
*   **MCP Tool**: A specific function hosted on the MCP server, such as `create_contact` or `book_appointment`.
*   **Private Integration Token (PIT)**: A token used for authentication, providing granular, permission-based access to the GHL API.

## Getting Started

To get started with the GoHighLevel MCP server, you need to:

1.  **Obtain a Private Integration Token (PIT)**: Generate a PIT from the "Settings → Private Integrations" section in your GoHighLevel account, ensuring to select the necessary scopes.
2.  **Configure Your Agent/Client**: Add the MCP endpoint and authentication headers to your agent's configuration.
3.  **Start Making Requests**: Use a compatible client or agent to send HTTP requests to the MCP server endpoint, allowing access to GoHighLevel data using natural language and tool calls.

## Further Reading

For more detailed information, please refer to the official GoHighLevel MCP documentation on the GoHighLevel Marketplace and related developer resources.
