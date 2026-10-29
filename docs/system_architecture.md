# System architecture

[Documentation index](README.md) · [AI infrastructure](models_and_ai_infrastructure.md) · [Operations](setup_and_operations.md)

These Mermaid diagrams describe the application design. They distinguish the authenticated web application from the Python API, which currently does not enforce an application authentication scheme.

## System context and trust boundaries

```mermaid
flowchart TB
    Person[Student, teacher or researcher]
    subgraph BrowserBoundary[User browser]
        UI[Next.js React interface]
        Speech[Browser speech APIs]
        Mermaid[Mermaid SVG rendering]
    end
    subgraph WebBoundary[Web application boundary]
        Web[Next.js route handlers]
        Auth[NextAuth JWT session]
        DB[(PostgreSQL via Prisma)]
    end
    subgraph PythonBoundary[Python service boundary]
        API[FastAPI routers and validation]
        Agent[LangGraph agents]
        Retrieval[Request-local document retrieval]
        Local[BLIP, CLIP and Tesseract]
    end
    Google[Google OAuth]
    NVIDIA[NVIDIA cloud API]
    Sources[Wikipedia, arXiv, search, websites and YouTube]
    ImageProviders[Hugging Face and AWS Bedrock]
    S3[(AWS S3)]
    Person --> UI
    UI --> Speech
    UI --> Mermaid
    UI --> Web
    Web --> Auth
    Auth <--> Google
    Web --> DB
    Web --> API
    UI -. Direct diagram generation .-> API
    API --> Agent
    API --> Retrieval
    API --> Local
    Agent --> NVIDIA
    Agent --> Sources
    API --> ImageProviders
    API --> S3
```

Normal chat and tool APIs check a web session and conversation ownership. Direct Python access and the browser's dedicated diagram request do not inherit those checks. The Next.js `/microservice/:path*` rewrite is a forwarding rule, not an authentication guard. Deployment must account for both access paths.

## Source components

```mermaid
flowchart LR
    subgraph Web[web/src]
        Pages[app pages and layouts]
        Components[components and hooks]
        Routes[app/api route handlers]
        Schema[lib/schema and prisma client]
        Pages --> Components
        Components --> Routes
        Routes --> Schema
    end
    subgraph Python[microservice]
        App[app.py]
        API[api/routes and api/requests]
        Assistant[services/assistant]
        Router[services/router]
        Images[services/images]
        Graph[agents/graph]
        NVIDIA[models/nvidia]
        RAG[services/rag]
        Tools[tools/generic_tools and custom_tools]
        Files[utils/files and image_captioning]
        ImageModels[models/flux and stable_diffusion]
        App --> API
        API --> Assistant
        API --> Router
        API --> Images
        Assistant --> Graph
        Graph --> NVIDIA
        Graph --> Tools
        Assistant --> RAG
        RAG --> Files
        Router --> NVIDIA
        Images --> ImageModels
    end
    Routes --> API
```

`app.py` composes the routers, CORS and exception handlers. The assistant service owns agent selection and text diagnostics; it creates request-local retrieval state. The image service owns provider selection and fallback. Llama remains a separate inactive source file and is not part of the active dependency graph.

## General chat sequence

```mermaid
sequenceDiagram
    actor User
    participant UI as Browser chat
    participant Web as Next.js /api/chat
    participant DB as PostgreSQL
    participant API as FastAPI /generate
    participant Route as NVIDIA classifier
    participant RAG as Local retrieval
    participant Agent as Research graph
    participant Cloud as NVIDIA cloud
    User->>UI: Prompt, optional files
    UI->>Web: Conversation ID, history, content, files
    Web->>DB: Check conversation owner
    DB-->>Web: Conversation
    Web->>DB: Save user message and update time
    Web->>API: Prompt, user/assistant history, files
    API->>Route: Classify current prompt
    Route-->>API: text or image and description
    alt text request
        opt Current request contains files
            API->>RAG: Extract, split, embed and retrieve
            RAG-->>Agent: Up to four labeled passages
        end
        API->>Agent: Prompt and history
        Agent->>Cloud: Model messages and tool schemas
        Cloud-->>Agent: Tool calls or final answer
        Note over Agent,Cloud: Tool calls loop through ToolNode when requested
        Agent-->>API: Final answer and diagnostics
    else image request
        Note over API: Flux generation with Stable Diffusion fallback, then S3 upload
    end
    API-->>Web: Model, text or image URL, metrics
    Web->>DB: Save bot message and main-chat metrics
    Web-->>UI: Saved messages and attachment names
    UI-->>User: Render response
```

The classifier is invoked for `/generate`; `/generate-chat` and `/generate-image` bypass that classification step. The user message is saved before upstream generation, so a provider failure can leave an unmatched user message. The web database operations and external generation are not one transaction.

## LangGraph execution

```mermaid
flowchart TD
    Start([START]) --> State[Invocation-local MessagesState]
    State --> Model[Agent node: system prompt plus current messages]
    Model --> Condition{Last AI message contains tool calls?}
    Condition -->|Yes, research agent| ToolNode[Execute registered tools]
    ToolNode --> Result[Append tool results or tool errors]
    Result --> Model
    Condition -->|No| End([END and final answer])
    Model -. Step limit exceeded .-> Failure[Request failure response]
```

Only the research graph binds tools. The diagram and YouTube graphs run a specialist model node and terminate. There is no persistent graph memory; callers supply history on each request. The 16-step recursion setting bounds graph steps, including both model and tool nodes.

## Attachment retrieval and image processing

```mermaid
flowchart TD
    Files[Current request attachments] --> Extension{File type}
    Extension -->|PDF| PDF[pypdf text extraction]
    Extension -->|TXT or MD| Text[UTF-8 text decoding]
    Extension -->|PNG or JPEG| Image[RGB image]
    Image --> DIP[Blur, contrast, brightness, sharpness, edge blend, grayscale contrast]
    DIP --> BLIP[BLIP caption]
    PDF --> Docs[LangChain documents with source filenames]
    Text --> Docs
    BLIP --> Docs
    Docs --> Split[Recursive character splitter: 1000 and overlap 150]
    Split --> Embed[Cached MiniLM model on CPU]
    Embed --> FAISS[(New request-local FAISS index)]
    Query[Current question] --> Search[Similarity retrieval, k equals 4]
    FAISS --> Search
    Search --> Context[Filename-labeled context]
    Context --> Agent[NVIDIA research agent]
    OCRFiles[OCR endpoint image files] --> Tesseract[Tesseract directly]
    Tesseract --> OCRText[Extracted text response]
```

The BLIP transformations are heuristics, not learned detection or segmentation. OCR is a separate route. An uploaded scanned PDF is not automatically rasterized into OCR images. The text retrieval index is discarded after the request; only the embedding model is shared. Image generation currently computes inherited retrieval context but does not use it to condition the output.

## Specialist and image workflows

```mermaid
flowchart LR
    Youtube[YouTube URL in prompt] --> Transcript[Retrieve available transcript]
    Transcript --> VideoAgent[Video specialist without research tools]
    VideoAgent --> Summary[Markdown summary and review questions]
    Description[Diagram description and current code] --> DiagramAgent[Mermaid specialist without tools]
    DiagramAgent --> Code[Mermaid code]
    Code --> Render[Browser parse and SVG render]
    ImagePrompt[Image request] --> Flux[Flux primary]
    Flux -->|Success| PNG[PNG bytes]
    Flux -->|Failure| SD[Stable Diffusion fallback]
    SD --> PNG
    PNG --> Upload[S3 upload]
    Upload --> URL[Image URL]
    PNG --> CLIP[CLIP diagnostic]
```

The image providers include their own safer-wording retries; fallback can also occur when the primary cannot initialize. The backend does not parse or validate generated Mermaid. A malformed diagram is detected by browser rendering, which displays an error instead of an automatic repair.

## Data model and persistence

```mermaid
erDiagram
    USER ||--o{ CONVERSATION : owns
    CONVERSATION ||--o{ CHAT : contains
    USER {
        string id PK
        string email
        string name
        string image
        datetime createdAt
        datetime updatedAt
    }
    CONVERSATION {
        string id PK
        string userId FK
        string title
        enum variant
        boolean isArchived
        datetime startedAt
        datetime lastUpdated
    }
    CHAT {
        string id PK
        string conversationId FK
        enum sender
        enum type
        string model
        string content
        string imageUrl
        json performanceMetrics
        datetime createdAt
        datetime updatedAt
    }
```

The [Prisma schema](../web/prisma/schema.prisma) defines chat/image types and conversation variants for general chat, notes, YouTube, diagrams and the image-filter placeholder. Foreign keys cascade on user/conversation deletion. There are no separate attachment, document-chunk, vector, tool-trace or learner-profile tables. S3 image objects are not shown as relational entities and are not automatically deleted by a Prisma cascade.

## Existing Compose deployment description

```mermaid
flowchart LR
    Browser[Browser] -->|Host port 3000| Web[Published sophianet-web image tag 4]
    Browser -. Host port 8000 .-> API[Published sophianet-microservice image tag 2]
    Web -->|Shared bridge network| API
    Web --> DB[(Externally configured PostgreSQL)]
    Web --> Google[Google OAuth]
    API --> NVIDIA[NVIDIA cloud]
    API --> Providers[Image and research providers]
    API --> S3[(S3)]
```

The [Compose file](../docker-compose.yml) references published image tags and injects separate `.env` files. It does not build the local source, define a PostgreSQL service, mount a durable model cache, configure healthchecks, add a job queue or provision provider resources. Consequently, starting those image tags does not establish that the local refactor is running. The Python Dockerfile also does not currently install Tesseract's system executable. No container was built or deployment verified for this documentation task.
