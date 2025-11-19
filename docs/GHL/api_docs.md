# GoHighLevel (GHL) API Documentation

This document provides a summary of the GoHighLevel (GHL) API, based on the official documentation.

## Overview

GoHighLevel is a comprehensive marketing and CRM platform. The GHL API provides programmatic access to the platform's features, allowing developers to build integrations and automate workflows.

## API Versions

GHL currently has two API versions:

*   **API V1**: The legacy API. It is being deprecated and should not be used for new integrations.
*   **API V2**: The current and recommended API version. It is built on modern standards, including OAuth 2.0, and is where all new features and endpoints will be added.

## Key Concepts

*   **Locations**: Sub-accounts within a GHL agency that represent individual businesses.
*   **Contacts**: Leads and customers within a location.
*   **Calendars**: Calendars for booking appointments.
*   **Opportunities**: Deals or potential sales in a pipeline.
*   **Workflows**: Automated sequences of actions that can be triggered by various events.

## API Reference

The GHL API V2 is a RESTful API with endpoints for managing a wide range of resources, including:

*   **Contacts**: Create, read, update, and delete contacts.
*   **Calendars**: Manage calendars and appointments.
*   **Opportunities**: Manage opportunities in pipelines.
*   **Workflows**: Trigger workflows for contacts.
*   **Conversations**: Send and receive SMS and email messages.

## Authentication

API V2 uses two primary authentication methods:

*   **OAuth 2.0**: For third-party applications that need to access data from multiple GHL accounts.
*   **Private Integration Tokens (PITs)**: For internal tools and server-side scripts that operate on a single GHL account.

## Further Reading

For more detailed information, please refer to the official GoHighLevel API documentation:

*   **API V2 Documentation**: [https://highlevel.stoplight.io/docs/integrations/620c057a1849a-go-high-level-api-docs](https://highlevel.stoplight.io/docs/integrations/620c057a1849a-go-high-level-api-docs)
*   **Developer Portal**: [https://developers.gohighlevel.com/](https://developers.gohighlevel.com/)
