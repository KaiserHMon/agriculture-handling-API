# Architecture & Technical Documentation

Welcome to the documentation directory for the Agriculture Handling API. This directory is organized to help developers understand the architecture, design choices, and system design patterns of the project.

## Directory Layout
* **[adr/](file:///C:/Proyectos/Api-AgricultureHandling/docs/adr/)**: Architecture Decision Records (ADRs) tracking historical design decisions and patterns.
* **[specs/](file:///C:/Proyectos/Api-AgricultureHandling/openspec/specs/)**: Detailed functional and technical specifications for new features and tasks.

## Active Architecture Decision Records (ADRs)
* **[ADR 0001: Transaction Boundaries and Session Management](file:///C:/Proyectos/Api-AgricultureHandling/docs/adr/0001-transaction-boundaries.md)** - Explains the boundary rules for transaction commits and rollbacks across the service and repository layers.
* **[ADR 0002: Asynchronous Background Processing with Celery](file:///C:/Proyectos/Api-AgricultureHandling/docs/adr/0002-celery-background-tasks.md)** - Documents the setup, worker runtime, and configuration for async background queues.
* **[ADR 0003: Auth0 Authentication and Role-Based Access Control](file:///C:/Proyectos/Api-AgricultureHandling/docs/adr/0003-auth0-integration.md)** - Details JWT token verification via JWKS, user provisioning, and role-based route constraints.
