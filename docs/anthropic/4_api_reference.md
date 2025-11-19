# 4. Claude API Reference

This document provides a detailed summary of the key API endpoints and parameters for the Claude API.

## Core Concepts

*   **Messages**: The primary way to interact with the Claude API. You send a message to the API and receive a response.
*   **Tools**: Functions that the model can call to perform actions.
*   **Skills**: Reusable task components that extend Claude's capabilities.

## Key API Endpoints

### `/v1/messages`

This is the main endpoint for interacting with the Claude API. You send a `POST` request to this endpoint with a JSON body containing the message you want to send to the model.

**Key Parameters**:

*   `model` (string, required): The ID of the model you want to use (e.g., `claude-3-5-sonnet-20240620`).
*   `messages` (array, required): A list of messages that make up the conversation history.
    *   `role` (string, required): The role of the message sender. Can be `user` or `assistant`.
    *   `content` (string or array, required): The content of the message.
*   `max_tokens` (integer, required): The maximum number of tokens to generate in the response.
*   `temperature` (number, optional): Controls the randomness of the output. Lower values are more deterministic, while higher values are more creative.
*   `tools` (array, optional): A list of tools that the model can use.
*   `tool_choice` (object, optional): Controls how the model uses tools.

**Example Response**:

```json
{
  "id": "msg_013C6K2i2A4i4z4M41D4i2s1",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you today?"
    }
  ],
  "model": "claude-3-5-sonnet-20240620",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 12,
    "output_tokens": 10
  }
}
```

### `/v1/skills`

This endpoint is used to manage skills.

*   `POST /v1/skills`: Create a new skill.
*   `GET /v1/skills/{skill_id}`: Retrieve a skill.
*   `PATCH /v1/skills/{skill_id}`: Update a skill.
*   `DELETE /v1/skills/{skill_id}`: Delete a skill.

### `/v1/files`

This endpoint is used to manage files.

*   `POST /v1/files`: Upload a file.
*   `GET /v1/files/{file_id}`: Retrieve a file.
*   `DELETE /v1/files/{file_id}`: Delete a file.

## Further Reading

For a complete and detailed API reference, please refer to the official Anthropic API documentation.