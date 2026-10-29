# Setup and operations

[Documentation index](README.md) · [Models](models_and_ai_infrastructure.md) · [Limitations](evaluation_and_limitations.md)

Commands below are instructions for a local setup. This documentation task did not change application dependencies, migrate a database, start services, build containers or contact providers. Preserve existing `.env` files and apply database migrations only to the intended database.

## Prerequisites

- The `sophianet-venv` Conda environment, using Python 3.11 for compatibility with the existing Python Dockerfile.
- Node.js and npm; the web Dockerfile currently targets Node 20.
- A reachable PostgreSQL database and Google OAuth application for authenticated web use.
- A valid NVIDIA API credential for text, routing, diagrams and transcript summaries.
- The Tesseract executable and desired language data for OCR; `pytesseract` is a Python wrapper, not the engine binary.
- Network access and disk space for public Hugging Face model downloads and external research services.
- Hugging Face/fal-ai and AWS Bedrock/S3 permissions for image generation. These are separate from the NVIDIA credential.

The existing `requirements.txt` includes substantial PyTorch/CUDA packages. Text-model inference runs in NVIDIA's cloud, but embeddings, BLIP and CLIP remain local model workloads. Verify platform compatibility before treating this dependency snapshot as a portable deployment package.

## Python configuration

The [microservice example environment](../microservice/.env.example) defines:

| Variable | Use |
| --- | --- |
| `NVIDIA_API_KEY` | Required for active language-model requests |
| `NVIDIA_MODEL` | Optional override; default `nvidia/nemotron-3.5-lightning-30b-a3b` |
| `PORT` | Used when running `python app.py`; default 8000 |
| `HF_TOKEN` | Existing Flux/Hugging Face inference credential |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS SDK credentials when this credential method is used |
| `AWS_DEFAULT_REGION` | AWS SDK default region; example uses `us-west-2` |
| `GROQ_API_KEY` | Retained for inactive Llama code; unnecessary for active text paths |

The AWS SDK may also use its normal profile/role credential chain; source code does not require embedded static keys. Bedrock runtime/model settings and S3 bucket/prefix live in [configuration files](../microservice/config/). The S3 helper creates its own boto3 client and uses that client's resolved region for the public URL; the `AWS_S3_REGION` dictionary entry is not explicitly passed into that helper's client construction.

For a new setup, copy the example to `.env` only if that file does not already exist, then fill in credentials privately. Do not commit real environment files. Model output limits, sampling, chunk sizes, timeout and retry settings are Python configuration, rather than separate environment variables for every knob.

```bash
conda activate sophianet-venv
cd microservice
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Alternatively, `python app.py` uses `PORT`. Uvicorn's CLI `--port` is independent of that application entrypoint variable. Local process liveness is available at `http://localhost:8000/health`; interactive FastAPI API documentation is at `http://localhost:8000/docs`.

MiniLM public embeddings download anonymously and run on CPU. They do not need `HF_TOKEN`. A prior implementation-session check returned HTTP 401 for the configured HF token; verify or refresh that credential before relying on Flux. This is an earlier snapshot, not a current credential audit. BLIP and CLIP downloads follow their existing Transformers configuration and should be checked separately.

## Web configuration and startup

The [web example environment](../web/.env.example) contains these names:

| Variable | Use |
| --- | --- |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth provider |
| `NEXTAUTH_SECRET` | JWT/session signing secret |
| `DATABASE_URL` | PostgreSQL datasource used by Prisma |
| `NODE_ENV` | Development or production mode |
| `MICROSERVICE_BASE_URL` | Server-side Python service URL, default `http://localhost:8000` |

Configure the Google OAuth callback for the web application's origin, for example `http://localhost:3000/api/auth/callback/google` in local development. NextAuth deployment configuration can also require its canonical application URL; the current `.env.example` does not list `NEXTAUTH_URL`.

For a new installation, create `web/.env` from the example without replacing an existing file. Configure the actual database and OAuth values, then run:

```bash
cd web
npm ci
npx prisma generate
npx prisma migrate deploy
npm run dev
```

`npm ci` runs the package's `postinstall` script, which already generates the Prisma client; the explicit generate command is useful when the schema changes or generation needs repeating. `prisma migrate deploy` applies the committed migration history to the configured database; review the target and migration changes first. No database is provisioned by the workspace Compose file.

The standard scripts are `dev`, `build`, `start`, `lint` and `postinstall`. A production web build/start can be performed with `npm run build` and `npm run start`; those commands were not run here. Because [next.config.ts](../web/next.config.ts) ignores ESLint and TypeScript errors during builds, a successful build would not substitute for separate lint and type checks.

### Browser-to-service URL caveat

[lib/config.ts](../web/src/lib/config.ts) uses a server-style `MICROSERVICE_BASE_URL` variable with a localhost fallback. The dedicated diagram component imports that constant in client code. Next.js does not generally expose unprefixed server variables to browser bundles, so a remote browser may use `http://localhost:8000` unless that path is changed or configured appropriately. This is a source-derived deployment concern; a remote-browser deployment was not tested.

The configured Next.js `/microservice/:path*` rewrite offers a same-origin forwarding route, but the current diagram component does not use that prefix. Avoid assuming the server-to-server URL and browser-reachable URL are interchangeable.

## Request examples

Direct API calls below exercise Python endpoints, which currently do not require a web session. They do not create or persist web conversations.

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/generate-chat \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Explain photosynthesis briefly.","session_history":[],"files":[]}'

curl -X POST http://localhost:8000/generate-chat \
  -F 'prompt=Summarize this document.' \
  -F 'session_history=[]' \
  -F 'files=@notes.txt'

curl -X POST http://localhost:8000/generate-diagram \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Draw a flow from input to output.","code":""}'
```

Model calls may incur provider usage and depend on quotas. See [features](features.md) for input limits and response fields. `/generate` adds a classification call; use `/generate-chat` when the caller has already selected text generation.

## Tests and diagnostic checks

From `microservice/`:

```bash
conda run -n sophianet-venv python -m unittest discover -s tests -v
conda run -n sophianet-venv python -m compileall -q app.py api agents config models services tools utils
conda run -n sophianet-venv python -m pip check
```

From `web/`, existing scripts and the installed compiler can be used for separate checks:

```bash
npm run lint
npx tsc --noEmit
```

These are recommended commands, not newly obtained passing results. The Python suite uses fake models/embeddings and mocked services. External-provider qualification should be recorded separately with commit, environment, endpoint, date, result and relevant output. Do not store credentials or private uploaded content in receipts.

## Storage and lifecycle

- PostgreSQL holds users, conversation metadata and chat content/URLs. Back up and restore this database according to the deployment's retention requirements.
- Document bytes and text retrieval indexes are not stored as reusable knowledge assets. Files must be attached again for fresh retrieval in a later request.
- S3 holds generated PNG objects under the configured prefix. Prisma row deletion does not remove those objects.
- The image upload helper defaults to public-read ACLs. Confirm that this matches both the bucket's access policy and the intended data exposure.
- Local model downloads use library-managed caches. The Compose file has no dedicated cache volume, so repeated container replacements may require downloading model assets again.
- Logging uses local files. Image captioning currently logs generated captions, and provider/tool errors can enter logs; consider content sensitivity and retention before using private documents.

## Deployment description and readiness

The root [Compose file](../docker-compose.yml) runs published `sophianet-web:4` and `sophianet-microservice:2` image references on a shared bridge network, exposing ports 3000 and 8000. It loads `web/.env` and `microservice/.env`, sets restart policies and defines a startup dependency. It does not verify service readiness or ensure those images contain the current local commits.

The Python Dockerfile installs build tools and curl, but does not install Tesseract. It also has no explicit model-cache provisioning or readiness check. These are operational gaps to resolve before claiming containerized OCR or a reproducible production deployment. No Docker build or image push is part of this documentation change.

## Failure interpretation

| Symptom | Likely boundary to inspect |
| --- | --- |
| `/health` works but chat fails | NVIDIA credential, model availability, quota, network or response validation |
| Chat works but attachment retrieval fails | File extraction, public model download, CPU embeddings, FAISS or document size |
| Image generation fails | HF/fal-ai or Bedrock access, provider initialization, S3 policy/region, CLIP/model downloads |
| OCR fails | Tesseract binary/language data, valid image bytes and supported extension |
| YouTube summary fails | Video/transcript availability, language selection, external restrictions or context length |
| Dedicated diagrams work locally but not remotely | Browser-visible URL, cross-origin access and backend reachability |
| Users cannot sign in or save chats | Google callback configuration, NextAuth secret and PostgreSQL/Prisma connectivity |

Liveness is a process check. Provider readiness, authenticated browser journeys, resource limits, S3 upload permissions and recovery behavior need their own checks.
