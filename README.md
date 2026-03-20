# Lattice: Gemini-Powered Healthcare Intelligence

Lattice is a healthcare document intelligence platform that converts messy, unstructured medical PDFs into structured, validated, and actionable records using Google Cloud Platform services.

## Public Repository Link
- https://github.com/<your-username>/Lattice

## Chosen Vertical
- Healthcare administrative workflow automation

## Application Use Case (6-7 Lines)
Lattice is a Gemini-powered healthcare app that transforms unstructured medical documents into structured patient intelligence.
It acts as a bridge between human intent (clinical decisions) and complex systems (claims, records, and care workflows).
Using Google Gemini Vision and Gemini LLM APIs, it extracts entities like patient details, encounters, claims, and conditions.
Structured outputs are stored in PostgreSQL and linked in Neo4j as a healthcare knowledge graph.
Care teams can track processing status, review validated JSON, and explore patient relationships in a single interface.
This reduces manual data entry, lowers transcription errors, and improves continuity of care.
The impact is strongest in high-volume hospitals and resource-constrained community clinics.

## Approach and Logic
1. Ingest PDF and store it in Google Cloud Storage.
2. Extract raw text with Gemini Vision.
3. Convert text to schema-validated JSON with Gemini LLM.
4. Persist structured data in PostgreSQL and relationships in Neo4j.
5. Expose document status and graph insights through a FastAPI + React interface.

## How the Solution Works
1. User uploads PDF from dashboard.
2. Backend validates MIME type, size, and page count.
3. File is stored in GCS (with local fallback for resilience).
4. Celery processes the document asynchronously.
5. Gemini Vision extracts document text.
6. Gemini LLM produces structured medical entities.
7. Entities are validated and ingested into PostgreSQL + Neo4j.

## Assumptions
- Google Cloud project has Gemini APIs enabled.
- Service account key is mounted at secrets/service-account.json.
- Documents are primarily English healthcare PDFs.
- At least one Gemini model is available for generateContent.

## Architecture
- Frontend: React + TypeScript
- API Layer: FastAPI
- Async Pipeline: Celery + Redis
- Relational Storage: PostgreSQL
- Graph Storage: Neo4j
- Cloud Services: GCS + Gemini APIs

## Google Cloud Services Integration
### Google Cloud Storage (GCS)
- Stores uploaded source documents securely.
- Supports document metadata and retrieval for processing.

### Gemini Vision API
- Extracts text from PDF content and preserves document context.

### Gemini LLM API
- Converts extracted text into structured healthcare entities.
- Uses deterministic JSON response settings for reliability.

### Reliability Strategy
- Ordered model fallback: gemini-2.5-flash -> gemini-flash-latest -> gemini-2.0-flash-lite
- Model availability error handling with retry
- Local storage fallback when cloud auth is unavailable

## Evaluation Focus Coverage
### 1) Code Quality
- Clear layering: routes, services, tasks, schemas
- Type hints and explicit response models
- Separation of concerns for maintainability

### 2) Security
- Secrets excluded from git (secrets/, .env)
- Input validation for file type, size, and page count
- Sanitized file names for storage paths
- Internal exception details not leaked in API errors

### 3) Efficiency
- Asynchronous background processing with Celery
- Gemini model candidate caching reduces repeated metadata calls
- Bounded pagination prevents expensive list queries

### 4) Testing and Maintainability
- Unit tests added for PDF validation behavior
- Pydantic schema validation for extraction output
- Service-level modularity for easier upgrades

### 5) Usability and Accessibility
- Upload and status workflows are simple and task-focused
- Form labels and ARIA attributes added for assistive technologies
- Clear status messaging and recoverable errors

### 6) Meaningful GCP Usage
- GCS for storage
- Gemini Vision for extraction
- Gemini LLM for structuring and interpretation
- GCP-first architecture with service-account authentication

## Complete Project Code in Repository
Repository includes:
- backend/ (FastAPI, Celery, services, migrations)
- frontend/ (React TypeScript UI)
- docker-compose.yml (local orchestration)
- README.md (setup, architecture, assumptions, and evaluation mapping)

## Local Run
```bash
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
```

## Validation
```bash
curl http://localhost:3000/health
docker compose exec backend pytest -q
```

## API Endpoints
- POST /documents/upload
- GET /documents/
- GET /documents/{document_id}
- GET /documents/{document_id}/graph
- GET /health

## License
MIT
