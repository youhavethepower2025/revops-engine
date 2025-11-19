# Vapi API Documentation

This document provides a summary of the Vapi API, based on the official documentation.

## Overview

Vapi is a platform for building, testing, and deploying voice AI applications. The Vapi API provides programmatic access to the platform's features, allowing developers to manage assistants, phone numbers, and calls.

## Key Concepts

*   **Assistants**: Voice-enabled AI agents that can be customized with different models, voices, and tools.
*   **Phone Numbers**: Numbers that can be assigned to assistants to handle inbound and outbound calls.
*   **Calls**: Instances of a conversation between a user and an assistant.

## API Reference

The Vapi API is a RESTful API with endpoints for managing the following resources:

*   **Assistants**:
    *   `POST /assistant`: Create a new assistant.
    *   `GET /assistant/{assistantId}`: Retrieve an assistant.
    *   `PATCH /assistant/{assistantId}`: Update an assistant.
    *   `GET /assistant`: List all assistants.
*   **Phone Numbers**:
    *   `POST /phone-number`: Import a Twilio phone number to Vapi.
    *   `GET /phone-number`: List all phone numbers.
    *   `PATCH /phone-number/{phoneNumberId}`: Update a phone number.
*   **Calls**:
    *   `GET /call/{callId}`: Retrieve a call.
    *   `GET /call`: List all calls.

## SDKs

Vapi provides SDKs for various languages and platforms, including:

*   Web (React, Vanilla JS)
*   Flutter
*   React Native
*   iOS
*   Python

## Further Reading

For more detailed information, please refer to the official Vapi API documentation at [docs.vapi.ai](https://docs.vapi.ai).
