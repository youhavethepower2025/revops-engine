# Railway API Documentation

This document provides a summary of the Railway API, based on the official documentation.

## Overview

The Railway API is a GraphQL API that allows you to programmatically manage your Railway projects and services. It is the same API that powers the Railway dashboard.

## Authentication

Authentication is done via API tokens. You can create a personal access token from your Railway account settings.

## API Reference

The Railway API is a GraphQL API, so it does not have traditional REST endpoints. Instead, you send queries and mutations to a single endpoint.

Some of the available queries and mutations include:

*   **Projects**: Create, read, update, and delete projects.
*   **Services**: Create, read, update, and delete services within a project.
*   **Deployments**: Manage deployments of your services.
*   **Variables**: Manage environment variables for your services.

## Further Reading

For more detailed information, please refer to the official Railway API documentation at [docs.railway.app/reference/public-api](https://docs.railway.app/reference/public-api).
