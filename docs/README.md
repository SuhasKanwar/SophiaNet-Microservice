# SophiaNet documentation

This documentation describes the source available on **2026-10-30**. It explains the implemented system and its research foundations without treating planned features or earlier test receipts as current production qualification.

## Reading guide

1. Read [project objectives](project_objectives.md) for the problem, intended users, scope and success criteria.
2. Use [features](features.md) to distinguish implemented behavior from partial and proposed capabilities.
3. Read [models and AI infrastructure](models_and_ai_infrastructure.md) for model IDs, cloud/local execution, tools, prompts and file-processing behavior.
4. Follow [system architecture](system_architecture.md) for Mermaid diagrams of the application, request flows, agent loop, retrieval, deployment and data model.
5. Use [setup and operations](setup_and_operations.md) to configure the Conda environment, Next.js application, provider credentials and database.
6. Consult [evaluation and limitations](evaluation_and_limitations.md) before interpreting metrics or making deployment and performance claims.
7. Read the [literature review](literature_review.md) and browse the [ten-paper research collection](research/README.md) for findings, gaps and a comparison to prior work.

## Documentation map

| Area | Primary source of truth |
| --- | --- |
| Active text model and sampling | [Python model configuration](../microservice/config/models.py) |
| Agent prompts | [System prompts](../microservice/config/prompts.py) |
| Agent execution | [Graph builder](../microservice/agents/graph.py), [assistant service](../microservice/services/assistant.py) |
| Python endpoints and input limits | [API routes](../microservice/api/routes/), [request schema](../microservice/api/requests.py) |
| Web authentication and persistence | [NextAuth options](../web/src/app/api/auth/%5B...nextauth%5D/options.ts), [Prisma schema](../web/prisma/schema.prisma) |
| Web-to-service protocol | [Chat route](../web/src/app/api/chat/route.ts), [tool-chat route](../web/src/app/api/tool-chat/route.ts) |
| Published-image deployment layout | [Compose file](../docker-compose.yml) |

## Status vocabulary

- **Implemented** means the code path exists and is connected to an endpoint or UI. It does not guarantee an available external provider or successful deployment.
- **Earlier verified** refers to the integration receipts described in the preceding implementation session and microservice README. This documentation task did not rerun those tests or providers.
- **Partial** means a capability has a limited path, such as OCR without a summarization stage or heuristics without a quality evaluation.
- **Proposed** means the feature is a design direction rather than delivered functionality.

Examples and diagrams show the current source design. Provider availability, credentials, quotas and model behavior can change independently of the application source. The research papers explain related methods; their benchmark results do not transfer automatically to SophiaNet.

## Scope of this documentation change

The documentation covers the web application, Python microservice, deployment description and research foundations.
