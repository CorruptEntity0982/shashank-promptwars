# Design Document: Bharat Health Timeline & Fraud Intelligence

## 1. System Overview

### 1.1 Executive Summary

The Bharat Health Timeline & Fraud Intelligence system is a production-grade AI-powered platform architected for rapid MVP deployment within a 48-hour hackathon constraint while maintaining clear pathways to AWS cloud scalability. The system transforms unstructured, multilingual medical documents into structured patient health timelines and detects insurance fraud patterns through intelligent document processing, natural language understanding, and rule-based anomaly detection.

This design prioritizes **architectural pragmatism over perfection**: every component choice balances hackathon velocity with production viability. The system employs a microservices-inspired architecture containerized via Docker, enabling local development without cloud costs while maintaining AWS migration readiness through deliberate abstraction boundaries.

### 1.2 Core Design Philosophy

**Hackathon-to-Production Duality**: The architecture embodies a dual nature—immediately deployable for demonstration while structurally prepared for production scaling. This is achieved through:

1. **Abstraction-First Design**: All external dependencies (OCR, LLM, storage) are abstracted behind interfaces, enabling seamless provider swapping
2. **Stateless Service Layer**: API and orchestration layers maintain no session state, enabling horizontal scaling
3. **Event-Driven Processing**: Asynchronous document processing via message queues decouples ingestion from computation
4. **Polyglot Persistence**: Purpose-built data stores (MongoDB for documents, Redis for caching) optimize for specific access patterns

**Technology Selection Criteria**:
- Open-source with permissive licenses (Apache 2.0, MIT)
- Docker-native with official container images
- Active community support and comprehensive documentation
- AWS-equivalent services available for migration
- Python ecosystem compatibility for rapid development


### 1.3 System Capabilities

The system delivers four primary capabilities:

1. **Intelligent Document Processing**: Converts scanned medical documents (JPEG, PNG, PDF) in English and Telugu into machine-readable text using OCR, with automatic language detection and mixed-script handling

2. **Medical Information Extraction**: Employs LLM-powered natural language understanding to extract structured medical entities (diagnoses, medications, procedures, lab results) with temporal information and patient demographics

3. **Chronological Timeline Construction**: Builds and maintains patient health timelines by normalizing dates, resolving ambiguities, and providing queryable access to medical history

4. **Fraud Pattern Detection**: Identifies suspicious patterns including duplicate claims, cost outliers, and temporal anomalies through rule-based analysis with confidence scoring

### 1.4 Key Architectural Decisions

**Decision 1: FastAPI over Flask/Django**
- **Rationale**: Async support for concurrent document processing, automatic OpenAPI documentation, Pydantic validation, and superior performance (3x faster than Flask in benchmarks)
- **Trade-off**: Smaller ecosystem than Django, but hackathon doesn't require admin interface or ORM

**Decision 2: LangChain + LangGraph for Orchestration**
- **Rationale**: Provides LLM abstraction (swap OpenAI/Bedrock/local models), built-in prompt management, and graph-based workflow orchestration for complex multi-step processing
- **Trade-off**: Additional dependency complexity, but eliminates custom LLM integration code

**Decision 3: MongoDB over PostgreSQL**
- **Rationale**: Schema flexibility for evolving medical event structures, native JSON storage for nested medical data, horizontal scaling readiness, and document-oriented model matches domain
- **Trade-off**: No ACID transactions across collections, but medical events are naturally isolated

**Decision 4: Google Vision API (with Textract migration path)**
- **Rationale**: Superior accuracy on multilingual documents (95%+ vs Tesseract's 85%), handles mixed scripts, and provides confidence scores
- **Trade-off**: Requires API key (free tier: 1000 pages/month), but architecture abstracts OCR behind interface for easy Textract swap

**Decision 5: Redis for Dual Purpose (Cache + Queue)**
- **Rationale**: Single dependency serves both caching (timeline queries) and task queue (document processing), reducing operational complexity
- **Trade-off**: Not a dedicated message broker like RabbitMQ, but sufficient for MVP scale



## 2. High-Level Architecture

### 2.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Actors & Systems                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│  │ Rural Clinic │      │ TPA Fraud    │      │  Physician   │          │
│  │ Administrator│      │  Analyst     │      │              │          │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘          │
│         │                     │                     │                   │
│         │ Upload Documents    │ Query Fraud Signals │ Query Timeline    │
│         │                     │                     │                   │
│         └─────────────────────┼─────────────────────┘                   │
│                               │                                          │
└───────────────────────────────┼──────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Bharat Health Timeline System                         │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                      API Gateway Layer                          │    │
│  │                    (FastAPI + Uvicorn)                          │    │
│  │  • Document Upload API  • Timeline Query API                    │    │
│  │  • Fraud Signal API     • Health Check API                      │    │
│  └────────────┬───────────────────────────────┬────────────────────┘    │
│               │                               │                         │
│               ▼                               ▼                         │
│  ┌────────────────────────┐     ┌────────────────────────────┐        │
│  │  Orchestration Layer   │     │    Query Service Layer     │        │
│  │  (LangChain/LangGraph) │     │   (Timeline + Fraud APIs)  │        │
│  │                        │     │                            │        │
│  │  • Document Processor  │     │  • Timeline Aggregator     │        │
│  │  • Event Extractor     │     │  • Fraud Signal Aggregator │        │
│  │  • Fraud Analyzer      │     │  • Cache Manager           │        │
│  └────────┬───────────────┘     └────────┬───────────────────┘        │
│           │                              │                             │
│           ▼                              ▼                             │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │              Processing Engine Layer                         │      │
│  ├──────────────┬──────────────┬──────────────┬────────────────┤      │
│  │  OCR Engine  │ NLP Extractor│ Normalizer   │ Fraud Detector │      │
│  │  (Vision API)│ (LLM-powered)│ (Rule-based) │ (Rule-based)   │      │
│  └──────┬───────┴──────┬───────┴──────┬───────┴────────┬───────┘      │
│         │              │              │                │               │
│         └──────────────┴──────────────┴────────────────┘               │
│                        │                                                │
│                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  Data Persistence Layer                      │      │
│  ├──────────────────┬──────────────────┬──────────────────────┤      │
│  │  MongoDB         │  Redis Cache     │  Local File Storage  │      │
│  │  (Events, Fraud) │  (Query Cache)   │  (Original Docs)     │      │
│  └──────────────────┴──────────────────┴──────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      External Services (Abstracted)                      │
├─────────────────────────────────────────────────────────────────────────┤
│  • Google Vision API (OCR) → AWS Textract (Production)                  │
│  • OpenAI/Bedrock (LLM) → Amazon Bedrock (Production)                   │
│  • Local File System → AWS S3 (Production)                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Architectural Layers

The system employs a **layered architecture** with clear separation of concerns:

**Layer 1: API Gateway (FastAPI)**
- Handles HTTP request/response lifecycle
- Performs input validation via Pydantic models
- Manages authentication and rate limiting
- Provides OpenAPI documentation
- Routes requests to appropriate service layers

**Layer 2: Orchestration Layer (LangChain/LangGraph)**
- Coordinates multi-step document processing workflows
- Manages LLM interactions with prompt templates
- Implements retry logic and error handling
- Maintains processing state machines
- Abstracts LLM provider differences

**Layer 3: Processing Engine Layer**
- **OCR Engine**: Text extraction from images
- **NLP Extractor**: Medical entity recognition
- **Normalizer**: Data standardization and structuring
- **Fraud Detector**: Pattern analysis and anomaly detection

**Layer 4: Data Persistence Layer**
- **MongoDB**: Primary data store for events, timelines, fraud signals
- **Redis**: Caching layer for query optimization and task queue
- **File System**: Original document storage with audit trail



### 2.3 Data Flow Architecture

```
Document Upload Flow:
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Client  │───▶│ FastAPI │───▶│  Redis   │───▶│ Worker  │───▶│ MongoDB  │
│         │    │  POST   │    │  Queue   │    │ Process │    │  Store   │
└─────────┘    └─────────┘    └──────────┘    └─────────┘    └──────────┘
                    │                               │
                    ▼                               ▼
              ┌──────────┐                    ┌──────────┐
              │   File   │                    │   OCR    │
              │  System  │                    │  Engine  │
              └──────────┘                    └──────────┘
                                                   │
                                                   ▼
                                              ┌──────────┐
                                              │   LLM    │
                                              │ Extract  │
                                              └──────────┘
                                                   │
                                                   ▼
                                              ┌──────────┐
                                              │ Normalize│
                                              └──────────┘
                                                   │
                                                   ▼
                                              ┌──────────┐
                                              │  Fraud   │
                                              │ Detector │
                                              └──────────┘

Timeline Query Flow:
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐
│ Client  │───▶│ FastAPI │───▶│  Redis   │───▶│  Client  │
│         │    │   GET   │    │  Cache   │    │ Response │
└─────────┘    └─────────┘    └────┬─────┘    └──────────┘
                                    │
                              Cache Miss
                                    │
                                    ▼
                               ┌──────────┐
                               │ MongoDB  │
                               │  Query   │
                               └──────────┘
                                    │
                                    ▼
                               ┌──────────┐
                               │  Redis   │
                               │  Store   │
                               └──────────┘
```

### 2.4 Deployment Architecture (Docker Compose)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Host (Laptop)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Docker Network: bharat-net               │ │
│  │                                                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   fastapi    │  │   worker     │  │   mongodb    │    │ │
│  │  │   :8000      │  │   (celery)   │  │   :27017     │    │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │ │
│  │         │                 │                 │             │ │
│  │         └─────────────────┼─────────────────┘             │ │
│  │                           │                               │ │
│  │                    ┌──────┴───────┐                       │ │
│  │                    │    redis     │                       │ │
│  │                    │    :6379     │                       │ │
│  │                    └──────────────┘                       │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Docker Volumes                           │ │
│  │  • mongodb-data    (Database persistence)                  │ │
│  │  • redis-data      (Cache persistence)                     │ │
│  │  • documents       (Original file storage)                 │ │
│  │  • logs            (Application logs)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Port Mappings
         ▼
┌─────────────────────┐
│  localhost:8000     │ → FastAPI
│  localhost:27017    │ → MongoDB (admin)
│  localhost:6379     │ → Redis (admin)
└─────────────────────┘
```



## 3. Component Breakdown

### 3.1 API Layer (FastAPI)

**Technology**: FastAPI 0.104+ with Uvicorn ASGI server

**Responsibilities**:
- HTTP request handling and routing
- Request validation using Pydantic models
- Response serialization to JSON
- API key authentication middleware
- Rate limiting (100 req/min per key)
- CORS configuration for future web UI
- OpenAPI/Swagger documentation generation
- Health check endpoints

**Key Design Decisions**:

1. **Async/Await Pattern**: All endpoints use `async def` to enable concurrent request handling without thread overhead. Critical for document upload endpoints that trigger long-running background tasks.

2. **Pydantic Models for Validation**: Request/response schemas defined as Pydantic models provide automatic validation, serialization, and OpenAPI schema generation. Example:
   ```python
   class DocumentUploadRequest(BaseModel):
       patient_id: str = Field(..., min_length=1, max_length=100)
       document_type: Literal["prescription", "lab_report", "discharge_summary"]
       language_hint: Optional[Literal["en", "te", "mixed"]] = None
   ```

3. **Dependency Injection**: FastAPI's dependency injection system manages database connections, authentication, and service layer instances, enabling clean testing and loose coupling.

4. **Background Tasks**: Uses FastAPI's `BackgroundTasks` for non-blocking operations like audit logging, while Redis queue handles heavy document processing.

**API Endpoints**:

```
POST   /api/v1/documents/upload          # Upload document for processing
GET    /api/v1/documents/{doc_id}/status # Check processing status
GET    /api/v1/patients/{patient_id}/timeline  # Retrieve patient timeline
GET    /api/v1/patients/{patient_id}/fraud     # Retrieve fraud signals
GET    /api/v1/health                    # Health check
GET    /api/v1/docs                      # OpenAPI documentation
```

**Error Handling Strategy**:
- 400: Validation errors (malformed requests)
- 401: Authentication failures
- 403: Authorization failures (insufficient permissions)
- 404: Resource not found
- 422: Semantic validation errors (e.g., invalid patient_id format)
- 429: Rate limit exceeded
- 500: Internal server errors (logged with trace IDs)
- 503: Service unavailable (database/Redis connection failures)

**Performance Optimizations**:
- Connection pooling for MongoDB (min: 10, max: 100 connections)
- Redis connection pool (max: 50 connections)
- Response compression (gzip) for payloads > 1KB
- ETag support for timeline queries (cache validation)
- Streaming responses for large timeline datasets



### 3.2 Orchestration Layer (LangChain + LangGraph)

**Technology**: LangChain 0.1+ with LangGraph for workflow orchestration

**Responsibilities**:
- Multi-step document processing workflow coordination
- LLM provider abstraction (OpenAI, Bedrock, local models)
- Prompt template management and versioning
- Retry logic with exponential backoff
- Processing state management
- Error recovery and fallback strategies

**Why LangChain + LangGraph**:

1. **Provider Agnosticism**: Single interface for OpenAI (hackathon), Bedrock (production), or local LLMs (cost optimization). Swap providers with configuration change, no code modification.

2. **Prompt Engineering Infrastructure**: Centralized prompt templates with variable interpolation, enabling rapid iteration without code changes. Example:
   ```python
   MEDICAL_EXTRACTION_PROMPT = PromptTemplate(
       template="""Extract medical entities from the following text in {language}.
       
       Text: {document_text}
       
       Extract:
       - Diagnoses (with ICD-10 codes if mentioned)
       - Medications (generic names, dosages, frequencies)
       - Procedures (with dates)
       - Lab results (test names, values, units)
       
       Return as JSON.""",
       input_variables=["language", "document_text"]
   )
   ```

3. **Graph-Based Workflows**: LangGraph enables complex, conditional processing flows with branching logic. Document processing workflow:
   ```
   START → OCR → Language Detection → [English Path | Telugu Path | Mixed Path]
         → Entity Extraction → Normalization → Fraud Detection → END
   ```

4. **Built-in Observability**: Automatic logging of LLM calls, token usage, latency, and costs. Critical for debugging and optimization.

**Document Processing Workflow (LangGraph State Machine)**:

```
┌─────────────────────────────────────────────────────────────────┐
│                  Document Processing Graph                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────┐                                                       │
│  │ START │                                                       │
│  └───┬───┘                                                       │
│      │                                                           │
│      ▼                                                           │
│  ┌────────────┐                                                 │
│  │ OCR_NODE   │ ─────error────▶ ┌──────────────┐              │
│  │ (Vision)   │                 │ ERROR_HANDLER│              │
│  └─────┬──────┘                 └──────────────┘              │
│        │                                                        │
│        ▼                                                        │
│  ┌──────────────┐                                              │
│  │ LANG_DETECT  │                                              │
│  │ (fasttext)   │                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│    ┌────┴────┬────────┐                                        │
│    ▼         ▼        ▼                                        │
│ ┌────┐   ┌────┐   ┌─────┐                                     │
│ │ EN │   │ TE │   │MIXED│                                     │
│ └─┬──┘   └─┬──┘   └──┬──┘                                     │
│   │        │         │                                         │
│   └────────┴─────────┘                                         │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │ ENTITY_EXTRACT  │                                          │
│   │ (LLM-powered)   │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │  NORMALIZE      │                                          │
│   │  (Rule-based)   │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │ FRAUD_DETECT    │                                          │
│   │ (Rule-based)    │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│   ┌─────────────────┐                                          │
│   │  STORE_EVENTS   │                                          │
│   │  (MongoDB)      │                                          │
│   └────────┬────────┘                                          │
│            │                                                    │
│            ▼                                                    │
│        ┌──────┐                                                │
│        │ END  │                                                │
│        └──────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**State Management**:
Each node in the graph operates on a shared state object:
```python
class ProcessingState(TypedDict):
    document_id: str
    patient_id: str
    raw_image: bytes
    ocr_text: Optional[str]
    detected_language: Optional[str]
    extracted_entities: Optional[List[Dict]]
    normalized_events: Optional[List[MedicalEvent]]
    fraud_signals: Optional[List[FraudSignal]]
    errors: List[str]
    processing_time_ms: int
```

**Error Handling & Retry Logic**:
- OCR failures: Retry 3x with exponential backoff (1s, 2s, 4s)
- LLM API failures: Retry 5x with jitter to avoid thundering herd
- Partial failures: Continue processing with degraded data (e.g., skip fraud detection if normalization fails)
- Circuit breaker: Disable LLM calls if error rate > 50% over 1 minute



### 3.3 OCR Layer (Google Vision API / AWS Textract)

**Technology**: Google Cloud Vision API (MVP) with abstraction for AWS Textract migration

**Responsibilities**:
- Convert image/PDF documents to machine-readable text
- Detect and preserve document structure (paragraphs, tables, lists)
- Provide confidence scores for extracted text
- Handle multilingual documents (English + Telugu)
- Extract text bounding boxes for spatial analysis

**Architecture Pattern: Strategy Pattern for OCR Abstraction**

```python
from abc import ABC, abstractmethod
from typing import List, Tuple

class OCRProvider(ABC):
    @abstractmethod
    async def extract_text(self, image_bytes: bytes, language_hints: List[str]) -> OCRResult:
        """Extract text from image with language hints."""
        pass

class OCRResult:
    text: str
    confidence: float
    language: str
    bounding_boxes: List[BoundingBox]
    processing_time_ms: int

class GoogleVisionOCR(OCRProvider):
    """MVP implementation using Google Vision API."""
    async def extract_text(self, image_bytes: bytes, language_hints: List[str]) -> OCRResult:
        # Implementation using google-cloud-vision library
        pass

class AWSTextractOCR(OCRProvider):
    """Production implementation using AWS Textract."""
    async def extract_text(self, image_bytes: bytes, language_hints: List[str]) -> OCRResult:
        # Implementation using boto3 textract client
        pass

class TesseractOCR(OCRProvider):
    """Fallback implementation using open-source Tesseract."""
    async def extract_text(self, image_bytes: bytes, language_hints: List[str]) -> OCRResult:
        # Implementation using pytesseract
        pass
```

**Provider Selection Logic**:
```python
def get_ocr_provider() -> OCRProvider:
    provider = os.getenv("OCR_PROVIDER", "google_vision")
    
    if provider == "google_vision":
        return GoogleVisionOCR(api_key=os.getenv("GOOGLE_VISION_API_KEY"))
    elif provider == "aws_textract":
        return AWSTextractOCR(region=os.getenv("AWS_REGION"))
    elif provider == "tesseract":
        return TesseractOCR()
    else:
        raise ValueError(f"Unknown OCR provider: {provider}")
```

**Google Vision API Configuration**:
- **Language Hints**: `["en", "te"]` for English and Telugu
- **Feature**: `TEXT_DETECTION` for dense text documents
- **Image Context**: Enable automatic orientation detection
- **Batch Processing**: Process up to 16 pages per API call for PDFs

**Performance Characteristics**:
- **Latency**: 1-3 seconds per page (Google Vision), 2-5 seconds (Textract)
- **Accuracy**: 95%+ on typed English, 90%+ on typed Telugu (Google Vision)
- **Cost**: $1.50 per 1000 pages (Google Vision), $1.50 per 1000 pages (Textract)
- **Rate Limits**: 1800 requests/minute (Google Vision free tier)

**Preprocessing Pipeline**:
Before OCR, apply image preprocessing to improve accuracy:
1. **Deskew**: Correct image rotation using Hough transform
2. **Denoise**: Apply Gaussian blur to reduce noise
3. **Binarization**: Convert to black/white using Otsu's method
4. **Contrast Enhancement**: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)

```python
import cv2
import numpy as np

def preprocess_image(image_bytes: bytes) -> bytes:
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Binarization
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Encode back to bytes
    _, encoded = cv2.imencode('.png', binary)
    return encoded.tobytes()
```

**Telugu Script Handling**:
- Google Vision supports Telugu Unicode (U+0C00 to U+0C7F)
- Handles mixed English-Telugu documents by detecting script boundaries
- Preserves Telugu diacritics and conjuncts
- Fallback to transliteration for ambiguous characters



### 3.4 LLM Layer (OpenAI / Bedrock / Local LLM)

**Technology**: LangChain abstraction over OpenAI GPT-4 (MVP), Amazon Bedrock Claude (Production), or local Llama models

**Responsibilities**:
- Medical entity extraction from unstructured text
- Named entity recognition (diagnoses, medications, procedures)
- Temporal expression extraction and normalization
- Relationship extraction (medication → diagnosis, procedure → diagnosis)
- Multilingual understanding (English and Telugu)

**LLM Selection Strategy**:

| Use Case | MVP (Hackathon) | Production (AWS) | Cost-Optimized |
|----------|----------------|------------------|----------------|
| Entity Extraction | GPT-4-Turbo | Claude 3 Sonnet (Bedrock) | Llama 3 70B (local) |
| Cost per 1M tokens | $10 input / $30 output | $3 input / $15 output | $0 (compute only) |
| Latency | 2-5 seconds | 1-3 seconds | 5-10 seconds |
| Accuracy | 95%+ | 93%+ | 85%+ |

**Prompt Engineering Strategy**:

The system uses **few-shot prompting** with medical domain examples to improve extraction accuracy:

```python
MEDICAL_ENTITY_EXTRACTION_PROMPT = """You are a medical information extraction system. Extract structured medical entities from the following clinical text.

EXAMPLES:

Input: "Patient diagnosed with Type 2 Diabetes Mellitus. Prescribed Metformin 500mg twice daily."
Output:
{
  "diagnoses": [
    {"name": "Type 2 Diabetes Mellitus", "icd10": "E11", "confidence": 0.95}
  ],
  "medications": [
    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "confidence": 0.98}
  ],
  "procedures": [],
  "lab_results": []
}

Input: "రోగికి మధుమేహం ఉంది. మెట్‌ఫార్మిన్ 500mg రోజుకు రెండుసార్లు."
Output:
{
  "diagnoses": [
    {"name": "Diabetes", "icd10": "E11", "confidence": 0.90}
  ],
  "medications": [
    {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily", "confidence": 0.95}
  ],
  "procedures": [],
  "lab_results": []
}

NOW EXTRACT FROM:
{document_text}

IMPORTANT:
- Return ONLY valid JSON
- Include confidence scores (0.0 to 1.0)
- Use generic drug names, not brand names
- Extract dates in ISO 8601 format (YYYY-MM-DD)
- If information is ambiguous, include multiple interpretations with lower confidence
"""
```

**Structured Output Enforcement**:

Use LangChain's `StructuredOutputParser` to enforce JSON schema compliance:

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class MedicalEntity(BaseModel):
    name: str = Field(description="Entity name")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")

class Diagnosis(MedicalEntity):
    icd10: Optional[str] = Field(description="ICD-10 code if available")

class Medication(MedicalEntity):
    dosage: Optional[str] = Field(description="Dosage amount and unit")
    frequency: Optional[str] = Field(description="Administration frequency")

class ExtractionResult(BaseModel):
    diagnoses: List[Diagnosis]
    medications: List[Medication]
    procedures: List[MedicalEntity]
    lab_results: List[Dict[str, Any]]

parser = PydanticOutputParser(pydantic_object=ExtractionResult)
```

**Token Optimization**:
- **Chunking**: Split long documents into 2000-token chunks with 200-token overlap
- **Prompt Caching**: Cache system prompts (reduces cost by 50% for repeated calls)
- **Selective Extraction**: Only extract entities relevant to timeline and fraud detection
- **Batch Processing**: Process multiple documents in single LLM call when possible

**Multilingual Handling**:
- **Language Detection**: Use fasttext for language identification before LLM call
- **Language-Specific Prompts**: Separate prompt templates for English and Telugu
- **Code-Switching**: Handle mixed-language text by processing sentence-by-sentence
- **Transliteration**: Convert Telugu medical terms to English equivalents for normalization

**Error Handling**:
- **Malformed JSON**: Retry with explicit JSON formatting instructions
- **Hallucinations**: Cross-validate extracted entities against medical ontologies (SNOMED CT, RxNorm)
- **Low Confidence**: Flag entities with confidence < 0.7 for manual review
- **Timeout**: Fallback to rule-based extraction if LLM call exceeds 30 seconds



### 3.5 Event Extraction Engine

**Responsibilities**:
- Transform LLM-extracted entities into structured MedicalEvent objects
- Extract temporal information (dates, durations, sequences)
- Extract patient demographics and provider information
- Assign unique event identifiers
- Link events to source documents

**Event Extraction Pipeline**:

```
Raw LLM Output → Entity Parser → Temporal Extractor → Patient Linker → Event Builder
```

**Temporal Expression Extraction**:

Uses `dateparser` library with custom rules for Indian date formats:

```python
import dateparser
from datetime import datetime
from typing import Optional, Tuple

class TemporalExtractor:
    # Indian date format patterns
    INDIAN_FORMATS = [
        "%d/%m/%Y",      # 15/08/2023
        "%d-%m-%Y",      # 15-08-2023
        "%d.%m.%Y",      # 15.08.2023
        "%d %b %Y",      # 15 Aug 2023
        "%d %B %Y",      # 15 August 2023
    ]
    
    def extract_date(self, text: str, context_date: Optional[datetime] = None) -> Tuple[Optional[datetime], float]:
        """
        Extract date from text with confidence score.
        
        Returns:
            (extracted_date, confidence_score)
        """
        # Try explicit date parsing
        for fmt in self.INDIAN_FORMATS:
            try:
                date = datetime.strptime(text, fmt)
                return (date, 0.95)
            except ValueError:
                continue
        
        # Try fuzzy parsing with dateparser
        settings = {
            'PREFER_DAY_OF_MONTH': 'first',
            'PREFER_DATES_FROM': 'past',
            'RELATIVE_BASE': context_date or datetime.now()
        }
        
        parsed = dateparser.parse(text, settings=settings, languages=['en', 'te'])
        if parsed:
            confidence = 0.8 if context_date else 0.6
            return (parsed, confidence)
        
        return (None, 0.0)
    
    def extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in days from text like '2 weeks', '3 months'."""
        import re
        
        patterns = {
            r'(\d+)\s*days?': 1,
            r'(\d+)\s*weeks?': 7,
            r'(\d+)\s*months?': 30,
            r'(\d+)\s*years?': 365,
        }
        
        for pattern, multiplier in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1)) * multiplier
        
        return None
```

**Patient Linking Strategy**:

Match extracted patient information to existing patient records using fuzzy matching:

```python
from fuzzywuzzy import fuzz
from typing import Optional

class PatientLinker:
    def __init__(self, db_client):
        self.db = db_client
    
    async def link_patient(self, extracted_info: Dict) -> Optional[str]:
        """
        Link extracted patient info to existing patient ID.
        
        Matching criteria (in order of priority):
        1. Exact patient ID match
        2. Phone number match
        3. Fuzzy name + DOB match (>90% similarity)
        4. Create new patient if no match
        """
        # Try exact ID match
        if patient_id := extracted_info.get("patient_id"):
            if await self.db.patients.find_one({"_id": patient_id}):
                return patient_id
        
        # Try phone number match
        if phone := extracted_info.get("phone"):
            if patient := await self.db.patients.find_one({"phone": phone}):
                return patient["_id"]
        
        # Try fuzzy name + DOB match
        if name := extracted_info.get("name"):
            candidates = await self.db.patients.find(
                {"name": {"$regex": name.split()[0], "$options": "i"}}
            ).to_list(length=100)
            
            for candidate in candidates:
                name_similarity = fuzz.ratio(name.lower(), candidate["name"].lower())
                
                if name_similarity > 90:
                    # Check DOB if available
                    if dob := extracted_info.get("date_of_birth"):
                        if candidate.get("date_of_birth") == dob:
                            return candidate["_id"]
                    else:
                        return candidate["_id"]
        
        # Create new patient
        new_patient_id = await self.create_patient(extracted_info)
        return new_patient_id
```

**Event Builder**:

Constructs standardized MedicalEvent objects:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class EventType(Enum):
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LAB_RESULT = "lab_result"
    VITAL_SIGN = "vital_sign"

@dataclass
class MedicalEvent:
    event_id: str                    # UUID
    patient_id: str                  # Foreign key to patient
    document_id: str                 # Source document
    event_type: EventType
    event_date: datetime
    event_date_confidence: float     # 0.0 to 1.0
    
    # Event-specific data
    diagnosis_code: Optional[str] = None      # ICD-10
    medication_name: Optional[str] = None     # Generic name
    medication_dosage: Optional[str] = None
    procedure_code: Optional[str] = None      # CPT code
    lab_test_name: Optional[str] = None
    lab_value: Optional[float] = None
    lab_unit: Optional[str] = None
    
    # Metadata
    provider_name: Optional[str] = None
    clinic_name: Optional[str] = None
    cost: Optional[float] = None
    confidence: float = 0.0
    
    # Audit
    created_at: datetime
    extracted_by: str                # "llm" or "manual"
```



### 3.6 Normalization Engine

**Responsibilities**:
- Standardize medical terminology to canonical forms
- Normalize dates to ISO 8601 format
- Map diagnoses to ICD-10 codes
- Map medications to generic names (RxNorm)
- Map procedures to CPT codes
- Handle incomplete or ambiguous data

**Normalization Pipeline**:

```
Raw Events → Terminology Mapper → Date Normalizer → Code Mapper → Validated Events
```

**Medical Terminology Normalization**:

```python
from typing import Dict, Optional
import re

class MedicalTerminologyNormalizer:
    def __init__(self):
        # Load medical dictionaries
        self.diagnosis_map = self._load_diagnosis_map()
        self.medication_map = self._load_medication_map()
        self.procedure_map = self._load_procedure_map()
    
    def normalize_diagnosis(self, raw_diagnosis: str) -> Dict[str, Any]:
        """
        Normalize diagnosis to standard form with ICD-10 code.
        
        Examples:
        - "Type 2 DM" → "Type 2 Diabetes Mellitus" (E11)
        - "HTN" → "Hypertension" (I10)
        - "మధుమేహం" → "Diabetes Mellitus" (E11)
        """
        # Clean input
        cleaned = raw_diagnosis.strip().lower()
        
        # Check abbreviation map
        if cleaned in self.diagnosis_map["abbreviations"]:
            return self.diagnosis_map["abbreviations"][cleaned]
        
        # Check Telugu translations
        if cleaned in self.diagnosis_map["telugu"]:
            return self.diagnosis_map["telugu"][cleaned]
        
        # Fuzzy match against standard terms
        from fuzzywuzzy import process
        match, score = process.extractOne(
            cleaned,
            self.diagnosis_map["standard_terms"].keys()
        )
        
        if score > 85:
            return self.diagnosis_map["standard_terms"][match]
        
        # Return as-is with flag for manual review
        return {
            "name": raw_diagnosis,
            "icd10": None,
            "confidence": 0.5,
            "needs_review": True
        }
    
    def normalize_medication(self, raw_medication: str) -> Dict[str, Any]:
        """
        Normalize medication to generic name.
        
        Examples:
        - "Glucophage" → "Metformin"
        - "Crocin" → "Paracetamol"
        - "మెట్‌ఫార్మిన్" → "Metformin"
        """
        cleaned = raw_medication.strip().lower()
        
        # Check brand-to-generic map
        if cleaned in self.medication_map["brands"]:
            return self.medication_map["brands"][cleaned]
        
        # Check Telugu translations
        if cleaned in self.medication_map["telugu"]:
            return self.medication_map["telugu"][cleaned]
        
        # Already generic name
        if cleaned in self.medication_map["generic_names"]:
            return self.medication_map["generic_names"][cleaned]
        
        # Fuzzy match
        from fuzzywuzzy import process
        match, score = process.extractOne(
            cleaned,
            list(self.medication_map["brands"].keys()) + 
            list(self.medication_map["generic_names"].keys())
        )
        
        if score > 80:
            return self.medication_map.get("brands", {}).get(
                match,
                self.medication_map["generic_names"].get(match)
            )
        
        return {
            "generic_name": raw_medication,
            "rxnorm_code": None,
            "confidence": 0.5,
            "needs_review": True
        }
```

**Date Normalization with Uncertainty Handling**:

```python
from datetime import datetime
from typing import Optional, Tuple
from enum import Enum

class DatePrecision(Enum):
    DAY = "day"           # Full date known
    MONTH = "month"       # Only month and year known
    YEAR = "year"         # Only year known
    APPROXIMATE = "approximate"  # Estimated date

class NormalizedDate:
    def __init__(
        self,
        date: datetime,
        precision: DatePrecision,
        confidence: float,
        original_text: str
    ):
        self.date = date
        self.precision = precision
        self.confidence = confidence
        self.original_text = original_text
    
    def to_iso8601(self) -> str:
        """Return ISO 8601 string with appropriate precision."""
        if self.precision == DatePrecision.DAY:
            return self.date.strftime("%Y-%m-%d")
        elif self.precision == DatePrecision.MONTH:
            return self.date.strftime("%Y-%m")
        elif self.precision == DatePrecision.YEAR:
            return self.date.strftime("%Y")
        else:
            return self.date.strftime("%Y-%m-%d") + "~"  # ~ indicates approximation

class DateNormalizer:
    def normalize(self, raw_date: str, context: Optional[datetime] = None) -> NormalizedDate:
        """
        Normalize date with uncertainty handling.
        
        Examples:
        - "15/08/2023" → 2023-08-15 (DAY, 0.95)
        - "Aug 2023" → 2023-08-01 (MONTH, 0.80)
        - "2023" → 2023-01-01 (YEAR, 0.70)
        - "last month" → 2023-07-01 (APPROXIMATE, 0.60)
        """
        # Try full date parsing
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
            try:
                date = datetime.strptime(raw_date, fmt)
                return NormalizedDate(date, DatePrecision.DAY, 0.95, raw_date)
            except ValueError:
                continue
        
        # Try month-year parsing
        for fmt in ["%m/%Y", "%b %Y", "%B %Y"]:
            try:
                date = datetime.strptime(raw_date, fmt)
                return NormalizedDate(date, DatePrecision.MONTH, 0.80, raw_date)
            except ValueError:
                continue
        
        # Try year-only parsing
        if re.match(r'^\d{4}$', raw_date):
            date = datetime(int(raw_date), 1, 1)
            return NormalizedDate(date, DatePrecision.YEAR, 0.70, raw_date)
        
        # Try relative date parsing
        import dateparser
        parsed = dateparser.parse(
            raw_date,
            settings={'RELATIVE_BASE': context or datetime.now()}
        )
        if parsed:
            return NormalizedDate(parsed, DatePrecision.APPROXIMATE, 0.60, raw_date)
        
        # Fallback to context date or current date
        fallback_date = context or datetime.now()
        return NormalizedDate(fallback_date, DatePrecision.APPROXIMATE, 0.30, raw_date)
```

**Code Mapping**:

The system maintains local dictionaries for common medical codes:

- **ICD-10 Codes**: ~70,000 diagnosis codes (subset of most common 5,000 for MVP)
- **RxNorm Codes**: ~200,000 medication codes (subset of most common 2,000 for MVP)
- **CPT Codes**: ~10,000 procedure codes (subset of most common 1,000 for MVP)

These dictionaries are loaded into memory at startup for fast lookup. For production, integrate with UMLS (Unified Medical Language System) API for comprehensive coverage.



### 3.7 Fraud Detection Engine

**Responsibilities**:
- Detect duplicate medical events (potential duplicate claims)
- Identify cost outliers (potential cost inflation)
- Flag temporal anomalies (impossible dates, suspicious sequences)
- Generate fraud signals with severity levels and confidence scores
- Maintain fraud detection rules and thresholds

**Fraud Detection Architecture**:

```
Medical Events → Rule Engine → Pattern Matchers → Fraud Signal Generator → MongoDB
                                    ↓
                            Statistical Analyzer
                                    ↓
                            Threshold Comparator
```

**Rule-Based Detection Patterns**:

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import timedelta
from enum import Enum

class FraudSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FraudType(Enum):
    DUPLICATE_EVENT = "duplicate_event"
    COST_OUTLIER = "cost_outlier"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    IMPOSSIBLE_SEQUENCE = "impossible_sequence"
    RAPID_SUCCESSION = "rapid_succession"

@dataclass
class FraudSignal:
    signal_id: str
    patient_id: str
    fraud_type: FraudType
    severity: FraudSeverity
    confidence: float
    description: str
    related_events: List[str]  # Event IDs
    detected_at: datetime
    metadata: Dict[str, Any]

class FraudDetectionRule(ABC):
    @abstractmethod
    async def detect(self, events: List[MedicalEvent]) -> List[FraudSignal]:
        """Detect fraud patterns in medical events."""
        pass

class DuplicateEventDetector(FraudDetectionRule):
    """Detect duplicate medical events within time window."""
    
    def __init__(self, time_window_days: int = 7, similarity_threshold: float = 0.90):
        self.time_window = timedelta(days=time_window_days)
        self.similarity_threshold = similarity_threshold
    
    async def detect(self, events: List[MedicalEvent]) -> List[FraudSignal]:
        signals = []
        
        # Sort events by date
        sorted_events = sorted(events, key=lambda e: e.event_date)
        
        for i, event1 in enumerate(sorted_events):
            for event2 in sorted_events[i+1:]:
                # Check if within time window
                if event2.event_date - event1.event_date > self.time_window:
                    break
                
                # Check if same event type
                if event1.event_type != event2.event_type:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(event1, event2)
                
                if similarity >= self.similarity_threshold:
                    # Determine severity based on provider
                    severity = (
                        FraudSeverity.HIGH 
                        if event1.clinic_name != event2.clinic_name 
                        else FraudSeverity.MEDIUM
                    )
                    
                    signals.append(FraudSignal(
                        signal_id=str(uuid.uuid4()),
                        patient_id=event1.patient_id,
                        fraud_type=FraudType.DUPLICATE_EVENT,
                        severity=severity,
                        confidence=similarity,
                        description=f"Duplicate {event1.event_type.value} detected within {self.time_window.days} days",
                        related_events=[event1.event_id, event2.event_id],
                        detected_at=datetime.now(),
                        metadata={
                            "similarity_score": similarity,
                            "time_difference_days": (event2.event_date - event1.event_date).days,
                            "same_provider": event1.clinic_name == event2.clinic_name
                        }
                    ))
        
        return signals
    
    def _calculate_similarity(self, event1: MedicalEvent, event2: MedicalEvent) -> float:
        """Calculate similarity between two events."""
        from fuzzywuzzy import fuzz
        
        if event1.event_type == EventType.DIAGNOSIS:
            return fuzz.ratio(
                event1.diagnosis_code or "",
                event2.diagnosis_code or ""
            ) / 100.0
        
        elif event1.event_type == EventType.MEDICATION:
            name_sim = fuzz.ratio(
                event1.medication_name or "",
                event2.medication_name or ""
            ) / 100.0
            dosage_sim = fuzz.ratio(
                event1.medication_dosage or "",
                event2.medication_dosage or ""
            ) / 100.0
            return (name_sim + dosage_sim) / 2
        
        elif event1.event_type == EventType.PROCEDURE:
            return fuzz.ratio(
                event1.procedure_code or "",
                event2.procedure_code or ""
            ) / 100.0
        
        return 0.0

class CostOutlierDetector(FraudDetectionRule):
    """Detect unusually expensive procedures."""
    
    def __init__(self, db_client, std_dev_threshold: float = 2.0):
        self.db = db_client
        self.std_dev_threshold = std_dev_threshold
        self.cost_stats = {}  # Cache for procedure cost statistics
    
    async def detect(self, events: List[MedicalEvent]) -> List[FraudSignal]:
        signals = []
        
        for event in events:
            if not event.cost or event.cost <= 0:
                continue
            
            # Get cost statistics for this procedure type
            stats = await self._get_cost_statistics(event)
            
            if not stats or stats["count"] < 10:
                # Insufficient data for statistical analysis
                continue
            
            # Calculate z-score
            z_score = (event.cost - stats["mean"]) / stats["std_dev"]
            
            if z_score > self.std_dev_threshold:
                severity = self._determine_severity(z_score)
                
                signals.append(FraudSignal(
                    signal_id=str(uuid.uuid4()),
                    patient_id=event.patient_id,
                    fraud_type=FraudType.COST_OUTLIER,
                    severity=severity,
                    confidence=min(0.95, z_score / 5.0),  # Cap at 0.95
                    description=f"Cost significantly exceeds typical range for {event.event_type.value}",
                    related_events=[event.event_id],
                    detected_at=datetime.now(),
                    metadata={
                        "actual_cost": event.cost,
                        "mean_cost": stats["mean"],
                        "std_dev": stats["std_dev"],
                        "z_score": z_score,
                        "expected_range": f"{stats['mean'] - 2*stats['std_dev']:.2f} - {stats['mean'] + 2*stats['std_dev']:.2f}"
                    }
                ))
        
        return signals
    
    async def _get_cost_statistics(self, event: MedicalEvent) -> Optional[Dict]:
        """Get cost statistics for event type from database."""
        cache_key = f"{event.event_type.value}:{event.procedure_code or event.diagnosis_code}"
        
        if cache_key in self.cost_stats:
            return self.cost_stats[cache_key]
        
        # Query database for historical costs
        pipeline = [
            {
                "$match": {
                    "event_type": event.event_type.value,
                    "cost": {"$gt": 0}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "mean": {"$avg": "$cost"},
                    "std_dev": {"$stdDevPop": "$cost"},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.db.medical_events.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats = result[0]
            self.cost_stats[cache_key] = stats
            return stats
        
        return None
    
    def _determine_severity(self, z_score: float) -> FraudSeverity:
        """Determine severity based on z-score."""
        if z_score > 4.0:
            return FraudSeverity.CRITICAL
        elif z_score > 3.0:
            return FraudSeverity.HIGH
        elif z_score > 2.5:
            return FraudSeverity.MEDIUM
        else:
            return FraudSeverity.LOW

class TemporalAnomalyDetector(FraudDetectionRule):
    """Detect temporal anomalies in medical events."""
    
    async def detect(self, events: List[MedicalEvent]) -> List[FraudSignal]:
        signals = []
        
        for event in events:
            # Check for future dates
            if event.event_date > datetime.now():
                signals.append(FraudSignal(
                    signal_id=str(uuid.uuid4()),
                    patient_id=event.patient_id,
                    fraud_type=FraudType.TEMPORAL_ANOMALY,
                    severity=FraudSeverity.HIGH,
                    confidence=0.99,
                    description="Event date is in the future",
                    related_events=[event.event_id],
                    detected_at=datetime.now(),
                    metadata={"event_date": event.event_date.isoformat()}
                ))
        
        # Check for rapid succession of high-cost procedures
        high_cost_events = [e for e in events if e.cost and e.cost > 10000]
        high_cost_events.sort(key=lambda e: e.event_date)
        
        window_size = 30  # days
        for i in range(len(high_cost_events) - 4):
            window_events = []
            start_date = high_cost_events[i].event_date
            
            for event in high_cost_events[i:]:
                if (event.event_date - start_date).days <= window_size:
                    window_events.append(event)
                else:
                    break
            
            if len(window_events) >= 5:
                signals.append(FraudSignal(
                    signal_id=str(uuid.uuid4()),
                    patient_id=high_cost_events[i].patient_id,
                    fraud_type=FraudType.RAPID_SUCCESSION,
                    severity=FraudSeverity.HIGH,
                    confidence=0.85,
                    description=f"{len(window_events)} high-cost procedures within {window_size} days",
                    related_events=[e.event_id for e in window_events],
                    detected_at=datetime.now(),
                    metadata={
                        "event_count": len(window_events),
                        "total_cost": sum(e.cost for e in window_events),
                        "time_window_days": window_size
                    }
                ))
        
        return signals
```

**Fraud Detection Orchestrator**:

```python
class FraudDetectionOrchestrator:
    def __init__(self, db_client):
        self.detectors = [
            DuplicateEventDetector(),
            CostOutlierDetector(db_client),
            TemporalAnomalyDetector()
        ]
    
    async def analyze_patient(self, patient_id: str) -> List[FraudSignal]:
        """Run all fraud detection rules for a patient."""
        # Fetch all events for patient
        events = await self.db.medical_events.find(
            {"patient_id": patient_id}
        ).to_list(length=None)
        
        all_signals = []
        for detector in self.detectors:
            signals = await detector.detect(events)
            all_signals.extend(signals)
        
        # Store signals in database
        if all_signals:
            await self.db.fraud_signals.insert_many(
                [signal.__dict__ for signal in all_signals]
            )
        
        return all_signals
```



### 3.8 Timeline Engine

**Responsibilities**:
- Construct chronological patient timelines from medical events
- Handle date ambiguities and incomplete information
- Support incremental timeline updates
- Provide efficient querying by date range and event type
- Maintain timeline consistency across document additions

**Timeline Construction Algorithm**:

```python
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TimelineEntry:
    date: datetime
    date_precision: DatePrecision
    events: List[MedicalEvent]
    confidence: float

class TimelineEngine:
    def __init__(self, db_client):
        self.db = db_client
    
    async def build_timeline(self, patient_id: str) -> List[TimelineEntry]:
        """
        Build chronological timeline for patient.
        
        Algorithm:
        1. Fetch all events for patient
        2. Sort by date (handling uncertainties)
        3. Group events by date
        4. Calculate aggregate confidence
        5. Return ordered timeline
        """
        # Fetch events
        events = await self.db.medical_events.find(
            {"patient_id": patient_id}
        ).to_list(length=None)
        
        if not events:
            return []
        
        # Sort events with uncertainty handling
        sorted_events = self._sort_with_uncertainty(events)
        
        # Group by date
        timeline = []
        current_date = None
        current_events = []
        
        for event in sorted_events:
            event_date = event.event_date.date()
            
            if current_date is None:
                current_date = event_date
                current_events = [event]
            elif event_date == current_date:
                current_events.append(event)
            else:
                # Create timeline entry for previous date
                timeline.append(self._create_timeline_entry(
                    current_date,
                    current_events
                ))
                current_date = event_date
                current_events = [event]
        
        # Add final entry
        if current_events:
            timeline.append(self._create_timeline_entry(
                current_date,
                current_events
            ))
        
        return timeline
    
    def _sort_with_uncertainty(self, events: List[MedicalEvent]) -> List[MedicalEvent]:
        """
        Sort events handling date uncertainties.
        
        Sorting rules:
        1. Primary: event_date (ascending)
        2. Secondary: date_confidence (descending - more certain dates first)
        3. Tertiary: created_at (ascending - older extractions first)
        """
        return sorted(
            events,
            key=lambda e: (
                e.event_date,
                -e.event_date_confidence,  # Negative for descending
                e.created_at
            )
        )
    
    def _create_timeline_entry(
        self,
        date: datetime.date,
        events: List[MedicalEvent]
    ) -> TimelineEntry:
        """Create timeline entry from grouped events."""
        # Calculate aggregate confidence
        avg_confidence = sum(e.event_date_confidence for e in events) / len(events)
        
        # Determine date precision (use lowest precision among events)
        precisions = [e.date_precision for e in events]
        min_precision = min(precisions, key=lambda p: p.value)
        
        return TimelineEntry(
            date=datetime.combine(date, datetime.min.time()),
            date_precision=min_precision,
            events=events,
            confidence=avg_confidence
        )
    
    async def query_timeline(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query patient timeline with filters.
        
        Returns paginated timeline with metadata.
        """
        # Build query filter
        query_filter = {"patient_id": patient_id}
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query_filter["event_date"] = date_filter
        
        if event_types:
            query_filter["event_type"] = {"$in": [et.value for et in event_types]}
        
        # Get total count
        total_count = await self.db.medical_events.count_documents(query_filter)
        
        # Fetch paginated events
        events = await self.db.medical_events.find(query_filter)\
            .sort("event_date", 1)\
            .skip(offset)\
            .limit(limit)\
            .to_list(length=limit)
        
        # Build timeline entries
        timeline = self._group_events_by_date(events)
        
        return {
            "patient_id": patient_id,
            "timeline": timeline,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(events) < total_count
            },
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "event_types": [et.value for et in event_types] if event_types else None
            }
        }
    
    async def update_timeline(self, patient_id: str, new_events: List[MedicalEvent]):
        """
        Incrementally update timeline with new events.
        
        This is more efficient than rebuilding entire timeline.
        """
        # Insert new events
        await self.db.medical_events.insert_many(
            [event.__dict__ for event in new_events]
        )
        
        # Invalidate cache for this patient
        await self._invalidate_cache(patient_id)
        
        # Trigger fraud detection for new events
        from .fraud_detection import FraudDetectionOrchestrator
        fraud_detector = FraudDetectionOrchestrator(self.db)
        await fraud_detector.analyze_patient(patient_id)
```

**Timeline Caching Strategy**:

```python
import hashlib
import json
from typing import Optional

class TimelineCacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour cache TTL
    
    def _generate_cache_key(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_types: Optional[List[EventType]]
    ) -> str:
        """Generate cache key from query parameters."""
        params = {
            "patient_id": patient_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "event_types": [et.value for et in event_types] if event_types else None
        }
        params_str = json.dumps(params, sort_keys=True)
        hash_digest = hashlib.md5(params_str.encode()).hexdigest()
        return f"timeline:{patient_id}:{hash_digest}"
    
    async def get_cached_timeline(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_types: Optional[List[EventType]]
    ) -> Optional[Dict]:
        """Retrieve cached timeline if available."""
        cache_key = self._generate_cache_key(patient_id, start_date, end_date, event_types)
        
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    async def cache_timeline(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        event_types: Optional[List[EventType]],
        timeline_data: Dict
    ):
        """Cache timeline query result."""
        cache_key = self._generate_cache_key(patient_id, start_date, end_date, event_types)
        
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(timeline_data)
        )
    
    async def invalidate_patient_cache(self, patient_id: str):
        """Invalidate all cached timelines for a patient."""
        pattern = f"timeline:{patient_id}:*"
        
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```



### 3.9 MongoDB Event Store

**Technology**: MongoDB 7.0+ (document-oriented NoSQL database)

**Responsibilities**:
- Persist medical events, patient records, fraud signals
- Support complex queries with indexing
- Provide atomic operations for data consistency
- Enable horizontal scaling through sharding (production)

**Database Schema Design**:

```javascript
// Collection: patients
{
  _id: ObjectId("..."),  // MongoDB auto-generated
  patient_id: "P123456",  // Business identifier
  name: "రాజు కుమార్",
  date_of_birth: ISODate("1985-03-15"),
  gender: "male",
  phone: "+919876543210",
  address: {
    street: "...",
    city: "Vijayawada",
    state: "Andhra Pradesh",
    pincode: "520001"
  },
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-15T10:30:00Z")
}

// Collection: medical_events
{
  _id: ObjectId("..."),
  event_id: "EVT-uuid-...",
  patient_id: "P123456",  // Foreign key to patients
  document_id: "DOC-uuid-...",  // Source document
  
  event_type: "diagnosis",  // diagnosis | medication | procedure | lab_result
  event_date: ISODate("2024-01-10T00:00:00Z"),
  event_date_confidence: 0.95,
  date_precision: "day",  // day | month | year | approximate
  
  // Event-specific fields (sparse schema)
  diagnosis_code: "E11",  // ICD-10
  diagnosis_name: "Type 2 Diabetes Mellitus",
  
  medication_name: "Metformin",
  medication_dosage: "500mg",
  medication_frequency: "twice daily",
  
  procedure_code: "99213",  // CPT
  procedure_name: "Office visit",
  
  lab_test_name: "HbA1c",
  lab_value: 7.2,
  lab_unit: "%",
  
  // Provider information
  provider_name: "Dr. వెంకట రావు",
  clinic_name: "రాజు క్లినిక్",
  clinic_location: "Vijayawada",
  
  // Financial
  cost: 1500.00,
  currency: "INR",
  
  // Metadata
  confidence: 0.92,
  extracted_by: "llm",  // llm | manual
  needs_review: false,
  
  // Audit
  created_at: ISODate("2024-01-15T10:30:00Z"),
  updated_at: ISODate("2024-01-15T10:30:00Z")
}

// Collection: documents
{
  _id: ObjectId("..."),
  document_id: "DOC-uuid-...",
  patient_id: "P123456",
  
  // File information
  filename: "prescription_2024_01_10.jpg",
  file_path: "/data/documents/2024/01/...",
  file_size_bytes: 245678,
  mime_type: "image/jpeg",
  
  // Processing status
  status: "completed",  // uploaded | processing | completed | failed
  processing_started_at: ISODate("2024-01-15T10:30:00Z"),
  processing_completed_at: ISODate("2024-01-15T10:32:15Z"),
  processing_time_ms: 135000,
  
  // OCR results
  ocr_text: "రోగి పేరు: రాజు కుమార్...",
  ocr_confidence: 0.89,
  detected_language: "te",
  
  // Extracted events
  event_ids: ["EVT-uuid-1", "EVT-uuid-2"],
  event_count: 2,
  
  // Errors
  errors: [],
  
  // Audit
  uploaded_by: "user_123",
  uploaded_at: ISODate("2024-01-15T10:30:00Z")
}

// Collection: fraud_signals
{
  _id: ObjectId("..."),
  signal_id: "FS-uuid-...",
  patient_id: "P123456",
  
  fraud_type: "duplicate_event",  // duplicate_event | cost_outlier | temporal_anomaly
  severity: "high",  // low | medium | high | critical
  confidence: 0.92,
  
  description: "Duplicate diagnosis detected within 7 days",
  
  related_events: ["EVT-uuid-1", "EVT-uuid-2"],
  
  metadata: {
    similarity_score: 0.95,
    time_difference_days: 3,
    same_provider: false
  },
  
  // Review status
  reviewed: false,
  reviewed_by: null,
  reviewed_at: null,
  review_notes: null,
  false_positive: false,
  
  // Audit
  detected_at: ISODate("2024-01-15T10:32:20Z")
}

// Collection: audit_logs
{
  _id: ObjectId("..."),
  log_id: "LOG-uuid-...",
  
  event_type: "document_upload",  // document_upload | timeline_query | fraud_signal_generated
  
  user_id: "user_123",
  patient_id: "P123456",
  
  request_details: {
    endpoint: "/api/v1/documents/upload",
    method: "POST",
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0..."
  },
  
  response_details: {
    status_code: 200,
    processing_time_ms: 45
  },
  
  timestamp: ISODate("2024-01-15T10:30:00Z")
}
```

**Indexing Strategy**:

```javascript
// patients collection
db.patients.createIndex({ patient_id: 1 }, { unique: true });
db.patients.createIndex({ phone: 1 });
db.patients.createIndex({ name: "text" });  // Full-text search

// medical_events collection
db.medical_events.createIndex({ patient_id: 1, event_date: -1 });  // Timeline queries
db.medical_events.createIndex({ event_id: 1 }, { unique: true });
db.medical_events.createIndex({ document_id: 1 });
db.medical_events.createIndex({ event_type: 1, event_date: -1 });
db.medical_events.createIndex({ diagnosis_code: 1 });
db.medical_events.createIndex({ medication_name: 1 });
db.medical_events.createIndex({ cost: 1 });  // Cost analysis
db.medical_events.createIndex({ created_at: -1 });  // Recent events

// Compound index for fraud detection
db.medical_events.createIndex({
  patient_id: 1,
  event_type: 1,
  event_date: -1
});

// documents collection
db.documents.createIndex({ document_id: 1 }, { unique: true });
db.documents.createIndex({ patient_id: 1, uploaded_at: -1 });
db.documents.createIndex({ status: 1 });

// fraud_signals collection
db.fraud_signals.createIndex({ signal_id: 1 }, { unique: true });
db.fraud_signals.createIndex({ patient_id: 1, detected_at: -1 });
db.fraud_signals.createIndex({ fraud_type: 1, severity: 1 });
db.fraud_signals.createIndex({ reviewed: 1 });

// audit_logs collection
db.audit_logs.createIndex({ timestamp: -1 });
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 });
db.audit_logs.createIndex({ patient_id: 1, timestamp: -1 });
db.audit_logs.createIndex({ event_type: 1, timestamp: -1 });

// TTL index for audit logs (auto-delete after 90 days)
db.audit_logs.createIndex(
  { timestamp: 1 },
  { expireAfterSeconds: 7776000 }  // 90 days
);
```

**Query Optimization Patterns**:

```python
# Efficient timeline query with projection
async def get_timeline_summary(patient_id: str):
    """Get timeline with only essential fields."""
    return await db.medical_events.find(
        {"patient_id": patient_id},
        {
            "_id": 0,
            "event_id": 1,
            "event_type": 1,
            "event_date": 1,
            "diagnosis_name": 1,
            "medication_name": 1,
            "procedure_name": 1
        }
    ).sort("event_date", -1).to_list(length=100)

# Aggregation pipeline for cost analysis
async def get_cost_statistics(event_type: str):
    """Calculate cost statistics for fraud detection."""
    pipeline = [
        {"$match": {"event_type": event_type, "cost": {"$gt": 0}}},
        {"$group": {
            "_id": "$event_type",
            "mean": {"$avg": "$cost"},
            "std_dev": {"$stdDevPop": "$cost"},
            "min": {"$min": "$cost"},
            "max": {"$max": "$cost"},
            "count": {"$sum": 1}
        }}
    ]
    return await db.medical_events.aggregate(pipeline).to_list(length=1)

# Bulk insert for batch processing
async def insert_events_batch(events: List[MedicalEvent]):
    """Efficiently insert multiple events."""
    await db.medical_events.insert_many(
        [event.__dict__ for event in events],
        ordered=False  # Continue on error
    )
```

**Data Consistency Patterns**:

```python
from motor.motor_asyncio import AsyncIOMotorClientSession

async def process_document_with_transaction(document_id: str, events: List[MedicalEvent]):
    """
    Process document with transactional consistency.
    
    Ensures document status and events are updated atomically.
    """
    async with await db.client.start_session() as session:
        async with session.start_transaction():
            # Update document status
            await db.documents.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "status": "completed",
                        "processing_completed_at": datetime.now(),
                        "event_count": len(events)
                    }
                },
                session=session
            )
            
            # Insert events
            if events:
                await db.medical_events.insert_many(
                    [event.__dict__ for event in events],
                    session=session
                )
```



### 3.10 Redis Cache & Task Queue

**Technology**: Redis 7.2+ (in-memory data structure store)

**Dual Purpose Architecture**:
1. **Cache Layer**: Store frequently accessed timeline queries
2. **Task Queue**: Manage asynchronous document processing jobs

**Cache Usage Patterns**:

```python
import redis.asyncio as redis
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cached value with TTL."""
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)  # Handle datetime serialization
        )
    
    async def delete(self, key: str):
        """Delete cached value."""
        await self.redis.delete(key)
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter (for rate limiting)."""
        return await self.redis.incrby(key, amount)
    
    async def expire(self, key: str, ttl: int):
        """Set expiration on existing key."""
        await self.redis.expire(key, ttl)
```

**Task Queue Implementation (Celery + Redis)**:

```python
from celery import Celery
from kombu import Queue

# Celery configuration
celery_app = Celery(
    'bharat_health',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'tasks.process_document': {'queue': 'document_processing'},
        'tasks.detect_fraud': {'queue': 'fraud_detection'},
    },
    
    # Queue configuration
    task_queues=(
        Queue('document_processing', routing_key='document.#'),
        Queue('fraud_detection', routing_key='fraud.#'),
    ),
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    
    # Task execution
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
)

@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str, patient_id: str):
    """
    Asynchronous document processing task.
    
    Retries up to 3 times with exponential backoff.
    """
    try:
        from .orchestration import DocumentProcessor
        
        processor = DocumentProcessor()
        result = processor.process(document_id, patient_id)
        
        return {
            "status": "success",
            "document_id": document_id,
            "events_extracted": len(result.events),
            "fraud_signals": len(result.fraud_signals)
        }
    
    except Exception as exc:
        # Retry with exponential backoff: 1min, 2min, 4min
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def detect_fraud(patient_id: str):
    """Asynchronous fraud detection task."""
    from .fraud_detection import FraudDetectionOrchestrator
    
    detector = FraudDetectionOrchestrator()
    signals = detector.analyze_patient(patient_id)
    
    return {
        "status": "success",
        "patient_id": patient_id,
        "signals_detected": len(signals)
    }
```

**Rate Limiting Implementation**:

```python
from fastapi import HTTPException, Request
from typing import Optional

class RateLimiter:
    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    async def check_rate_limit(self, api_key: str) -> bool:
        """
        Check if request is within rate limit.
        
        Uses sliding window algorithm with Redis.
        """
        key = f"rate_limit:{api_key}"
        
        # Get current count
        current = await self.redis.get(key)
        
        if current is None:
            # First request in window
            await self.redis.setex(key, self.window_seconds, 1)
            return True
        
        current_count = int(current)
        
        if current_count >= self.max_requests:
            return False
        
        # Increment counter
        await self.redis.incr(key)
        return True
    
    async def get_remaining_requests(self, api_key: str) -> int:
        """Get remaining requests in current window."""
        key = f"rate_limit:{api_key}"
        current = await self.redis.get(key)
        
        if current is None:
            return self.max_requests
        
        return max(0, self.max_requests - int(current))

# FastAPI middleware
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for FastAPI."""
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    rate_limiter = RateLimiter(request.app.state.redis)
    
    if not await rate_limiter.check_rate_limit(api_key):
        remaining = await rate_limiter.get_remaining_requests(api_key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": str(rate_limiter.window_seconds)
            }
        )
    
    response = await call_next(request)
    return response
```

**Cache Invalidation Strategy**:

```python
class CacheInvalidationManager:
    """Manage cache invalidation on data updates."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def invalidate_patient_timeline(self, patient_id: str):
        """Invalidate all cached timelines for a patient."""
        pattern = f"timeline:{patient_id}:*"
        await self._delete_pattern(pattern)
    
    async def invalidate_fraud_signals(self, patient_id: str):
        """Invalidate cached fraud signals for a patient."""
        pattern = f"fraud_signals:{patient_id}:*"
        await self._delete_pattern(pattern)
    
    async def invalidate_all_patient_data(self, patient_id: str):
        """Invalidate all cached data for a patient."""
        patterns = [
            f"timeline:{patient_id}:*",
            f"fraud_signals:{patient_id}:*",
            f"patient:{patient_id}"
        ]
        for pattern in patterns:
            await self._delete_pattern(pattern)
    
    async def _delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
```

**Redis Data Structures Usage**:

```python
# Sorted sets for leaderboards (e.g., most expensive procedures)
await redis.zadd("expensive_procedures", {
    "procedure_1": 50000,
    "procedure_2": 45000,
    "procedure_3": 40000
})

# Get top 10 expensive procedures
top_procedures = await redis.zrevrange("expensive_procedures", 0, 9, withscores=True)

# Hash maps for patient metadata
await redis.hset(f"patient:{patient_id}", mapping={
    "name": "రాజు కుమార్",
    "last_visit": "2024-01-15",
    "total_events": "25"
})

# Lists for recent activity
await redis.lpush(f"recent_uploads:{user_id}", document_id)
await redis.


## 4. Data Model Design

### 4.1 Core Domain Models

**Patient Entity**:
```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class Address(BaseModel):
    street: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"

class Patient(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    name: str = Field(..., min_length=1, max_length=200)
    date_of_birth: date
    gender: Literal["male", "female", "other"]
    phone: Optional[str] = Field(None, regex=r'^\+91\d{10}$')
    address: Optional[Address] = None
    created_at: datetime
    updated_at: datetime
```

**Medical Event Entity**:
```python
class MedicalEvent(BaseModel):
    event_id: str
    patient_id: str
    document_id: str
    event_type: EventType
    event_date: datetime
    event_date_confidence: float = Field(ge=0.0, le=1.0)
    date_precision: DatePrecision
    
    # Optional fields based on event type
    diagnosis_code: Optional[str] = None
    diagnosis_name: Optional[str] = None
    medication_name: Optional[str] = None
    medication_dosage: Optional[str] = None
    procedure_code: Optional[str] = None
    lab_test_name: Optional[str] = None
    lab_value: Optional[float] = None
    
    provider_name: Optional[str] = None
    clinic_name: Optional[str] = None
    cost: Optional[float] = Field(None, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    
    created_at: datetime
    updated_at: datetime
```

**Fraud Signal Entity**:
```python
class FraudSignal(BaseModel):
    signal_id: str
    patient_id: str
    fraud_type: FraudType
    severity: FraudSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    related_events: List[str]
    metadata: Dict[str, Any]
    reviewed: bool = False
    detected_at: datetime
```

### 4.2 MongoDB Indexing Strategy

**Performance Optimization**:
- Compound indexes for common query patterns
- Text indexes for full-text search
- TTL indexes for automatic data expiration
- Sparse indexes for optional fields

**Index Cardinality Analysis**:
- High cardinality: patient_id, event_id, document_id
- Medium cardinality: event_type, fraud_type, clinic_name
- Low cardinality: gender, severity, status

**Query Pattern Optimization**:
```javascript
// Timeline query: patient_id + date range
db.medical_events.createIndex({ patient_id: 1, event_date: -1 });

// Fraud detection: patient_id + event_type + date
db.medical_events.createIndex({ patient_id: 1, event_type: 1, event_date: -1 });

// Cost analysis: event_type + cost
db.medical_events.createIndex({ event_type: 1, cost: 1 });
```



## 5. Patient Timeline Architecture

### 5.1 Event Sourcing Approach

The timeline system uses an **event sourcing pattern** where medical events are immutable facts that build up patient history over time.

**Key Principles**:
1. **Immutability**: Events are never modified, only appended
2. **Temporal Ordering**: Events are sorted by occurrence date
3. **Incremental Updates**: New documents add events without rebuilding entire timeline
4. **Audit Trail**: Complete history of all medical events preserved

**Event Sourcing Benefits**:
- Complete audit trail for compliance
- Ability to reconstruct timeline at any point in time
- Support for temporal queries ("show me patient state on date X")
- Easy rollback and correction of errors

### 5.2 Timeline Query Abstraction

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

class TimelineQuery(ABC):
    """Abstract base for timeline queries."""
    
    @abstractmethod
    async def execute(self, patient_id: str) -> List[TimelineEntry]:
        pass

class DateRangeQuery(TimelineQuery):
    """Query timeline by date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
    
    async def execute(self, patient_id: str) -> List[TimelineEntry]:
        # Implementation
        pass

class EventTypeQuery(TimelineQuery):
    """Query timeline by event type."""
    
    def __init__(self, event_types: List[EventType]):
        self.event_types = event_types
    
    async def execute(self, patient_id: str) -> List[TimelineEntry]:
        # Implementation
        pass

class CompositeQuery(TimelineQuery):
    """Combine multiple queries with AND logic."""
    
    def __init__(self, queries: List[TimelineQuery]):
        self.queries = queries
    
    async def execute(self, patient_id: str) -> List[TimelineEntry]:
        # Execute all queries and intersect results
        pass
```

### 5.3 Timeline Visualization Format

```json
{
  "patient_id": "P123456",
  "patient_name": "రాజు కుమార్",
  "timeline": [
    {
      "date": "2024-01-15",
      "date_precision": "day",
      "confidence": 0.95,
      "events": [
        {
          "event_id": "EVT-001",
          "event_type": "diagnosis",
          "diagnosis_name": "Type 2 Diabetes Mellitus",
          "diagnosis_code": "E11",
          "provider": "Dr. వెంకట రావు",
          "clinic": "రాజు క్లినిక్",
          "confidence": 0.95
        },
        {
          "event_id": "EVT-002",
          "event_type": "medication",
          "medication_name": "Metformin",
          "dosage": "500mg",
          "frequency": "twice daily",
          "confidence": 0.98
        }
      ]
    },
    {
      "date": "2024-01-10",
      "date_precision": "day",
      "confidence": 0.90,
      "events": [
        {
          "event_id": "EVT-003",
          "event_type": "lab_result",
          "lab_test_name": "HbA1c",
          "lab_value": 7.2,
          "lab_unit": "%",
          "confidence": 0.92
        }
      ]
    }
  ],
  "summary": {
    "total_events": 3,
    "date_range": {
      "earliest": "2024-01-10",
      "latest": "2024-01-15"
    },
    "event_type_counts": {
      "diagnosis": 1,
      "medication": 1,
      "lab_result": 1
    }
  }
}
```



## 6. Fraud Detection Design

### 6.1 Rule-Based Detection Architecture

The fraud detection system employs a **rule-based approach** for the MVP, with clear extension points for machine learning models in production.

**Design Rationale**:
- Rule-based systems are explainable (critical for fraud investigation)
- No training data required (can deploy immediately)
- Deterministic behavior (easier to debug and validate)
- Fast execution (no model inference latency)
- Clear migration path to ML-enhanced detection

### 6.2 Detection Rule Hierarchy

```
FraudDetectionRule (Abstract Base)
├── DuplicateEventDetector
│   ├── ExactDuplicateRule
│   ├── FuzzyDuplicateRule
│   └── CrossProviderDuplicateRule
├── CostOutlierDetector
│   ├── StatisticalOutlierRule
│   ├── RegionalCostRule
│   └── HistoricalCostRule
└── TemporalAnomalyDetector
    ├── FutureDateRule
    ├── RapidSuccessionRule
    ├── ImpossibleSequenceRule
    └── BackdatingRule
```

### 6.3 Duplicate Billing Detection

**Algorithm**: Fuzzy matching with time window

```python
def detect_duplicates(events: List[MedicalEvent]) -> List[FraudSignal]:
    """
    Detect duplicate events using fuzzy matching.
    
    Algorithm:
    1. Sort events by date
    2. For each event, compare with events in 7-day window
    3. Calculate similarity score (0.0 to 1.0)
    4. If similarity > 0.90, flag as duplicate
    5. Higher severity if different providers
    """
    duplicates = []
    time_window = timedelta(days=7)
    
    for i, event1 in enumerate(events):
        for event2 in events[i+1:]:
            if event2.event_date - event1.event_date > time_window:
                break
            
            similarity = calculate_similarity(event1, event2)
            
            if similarity > 0.90:
                severity = (
                    FraudSeverity.HIGH 
                    if event1.clinic_name != event2.clinic_name 
                    else FraudSeverity.MEDIUM
                )
                
                duplicates.append(create_fraud_signal(
                    fraud_type=FraudType.DUPLICATE_EVENT,
                    severity=severity,
                    confidence=similarity,
                    events=[event1, event2]
                ))
    
    return duplicates
```

**Similarity Calculation**:
- Diagnosis: ICD-10 code exact match or name fuzzy match
- Medication: Generic name + dosage fuzzy match
- Procedure: CPT code exact match or name fuzzy match
- Lab Result: Test name exact match

### 6.4 Suspicious Pattern Detection

**Pattern 1: Rapid High-Cost Procedures**
```python
def detect_rapid_succession(events: List[MedicalEvent]) -> List[FraudSignal]:
    """
    Detect suspicious rapid succession of expensive procedures.
    
    Rule: 5+ procedures costing >₹10,000 each within 30 days
    """
    high_cost_events = [e for e in events if e.cost and e.cost > 10000]
    high_cost_events.sort(key=lambda e: e.event_date)
    
    signals = []
    window_size = 30  # days
    
    for i in range(len(high_cost_events) - 4):
        window_events = []
        start_date = high_cost_events[i].event_date
        
        for event in high_cost_events[i:]:
            if (event.event_date - start_date).days <= window_size:
                window_events.append(event)
            else:
                break
        
        if len(window_events) >= 5:
            signals.append(create_fraud_signal(
                fraud_type=FraudType.RAPID_SUCCESSION,
                severity=FraudSeverity.HIGH,
                confidence=0.85,
                events=window_events,
                metadata={
                    "event_count": len(window_events),
                    "total_cost": sum(e.cost for e in window_events),
                    "time_window_days": window_size
                }
            ))
    
    return signals
```

**Pattern 2: Cost Inflation**
```python
def detect_cost_outliers(events: List[MedicalEvent]) -> List[FraudSignal]:
    """
    Detect procedures with costs significantly above average.
    
    Rule: Cost > mean + 2*std_dev for procedure type
    """
    signals = []
    
    for event in events:
        if not event.cost:
            continue
        
        # Get historical cost statistics
        stats = get_cost_statistics(event.event_type, event.procedure_code)
        
        if not stats or stats["count"] < 10:
            continue
        
        # Calculate z-score
        z_score = (event.cost - stats["mean"]) / stats["std_dev"]
        
        if z_score > 2.0:
            signals.append(create_fraud_signal(
                fraud_type=FraudType.COST_OUTLIER,
                severity=determine_severity(z_score),
                confidence=min(0.95, z_score / 5.0),
                events=[event],
                metadata={
                    "actual_cost": event.cost,
                    "expected_range": f"{stats['mean'] - 2*stats['std_dev']:.2f} - {stats['mean'] + 2*stats['std_dev']:.2f}",
                    "z_score": z_score
                }
            ))
    
    return signals
```

### 6.5 Future ML Anomaly Extension

**Architecture for ML Integration**:

```python
class MLFraudDetector(FraudDetectionRule):
    """
    Machine learning-based fraud detector (future enhancement).
    
    Uses trained model to detect complex fraud patterns.
    """
    
    def __init__(self, model_path: str):
        self.model = self._load_model(model_path)
        self.feature_extractor = FeatureExtractor()
    
    async def detect(self, events: List[MedicalEvent]) -> List[FraudSignal]:
        # Extract features from events
        features = self.feature_extractor.extract(events)
        
        # Run model inference
        predictions = self.model.predict(features)
        
        # Convert predictions to fraud signals
        signals = self._predictions_to_signals(predictions, events)
        
        return signals
    
    def _load_model(self, model_path: str):
        """Load trained ML model (e.g., XGBoost, Random Forest)."""
        import joblib
        return joblib.load(model_path)

class FeatureExtractor:
    """Extract features for ML fraud detection."""
    
    def extract(self, events: List[MedicalEvent]) -> np.ndarray:
        """
        Extract features from medical events.
        
        Features:
        - Event frequency (events per month)
        - Cost statistics (mean, std, max)
        - Provider diversity (unique clinics)
        - Temporal patterns (gaps between events)
        - Event type distribution
        - Geographic patterns
        """
        features = []
        
        # Temporal features
        features.append(self._calculate_event_frequency(events))
        features.append(self._calculate_temporal_gaps(events))
        
        # Cost features
        features.extend(self._calculate_cost_statistics(events))
        
        # Provider features
        features.append(self._calculate_provider_diversity(events))
        
        # Event type features
        features.extend(self._calculate_event_distribution(events))
        
        return np.array(features)
```

**ML Model Training Pipeline (Future)**:
1. Collect labeled fraud cases from TPA analysts
2. Extract features from historical events
3. Train ensemble model (XGBoost + Random Forest)
4. Validate on held-out test set
5. Deploy model with A/B testing against rule-based system
6. Monitor model performance and retrain periodically



## 7. Multilingual Handling Strategy

### 7.1 Language Detection Pipeline

```
Document → OCR → Text Extraction → Language Detection → Language-Specific Processing
```

**Language Detection Library**: fasttext (Facebook's language identification model)

```python
import fasttext

class LanguageDetector:
    def __init__(self):
        # Load pre-trained fasttext model
        self.model = fasttext.load_model('lid.176.bin')
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect language with confidence score.
        
        Returns:
            (language_code, confidence)
            e.g., ('en', 0.95) or ('te', 0.89)
        """
        predictions = self.model.predict(text, k=1)
        language = predictions[0][0].replace('__label__', '')
        confidence = predictions[1][0]
        
        return (language, confidence)
    
    def detect_mixed(self, text: str) -> Dict[str, float]:
        """
        Detect multiple languages in mixed text.
        
        Returns language distribution:
        {'en': 0.6, 'te': 0.4}
        """
        sentences = self._split_sentences(text)
        language_counts = {}
        
        for sentence in sentences:
            lang, conf = self.detect(sentence)
            if conf > 0.7:  # Only count high-confidence detections
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # Normalize to percentages
        total = sum(language_counts.values())
        return {lang: count/total for lang, count in language_counts.items()}
```

### 7.2 OCR Language Handling

**Google Vision API Configuration**:
```python
from google.cloud import vision

def configure_ocr_for_multilingual(image_bytes: bytes) -> vision.TextAnnotation:
    """Configure OCR with language hints for English and Telugu."""
    client = vision.ImageAnnotatorClient()
    
    image = vision.Image(content=image_bytes)
    
    # Configure language hints
    image_context = vision.ImageContext(
        language_hints=['en', 'te']  # English and Telugu
    )
    
    # Perform OCR
    response = client.document_text_detection(
        image=image,
        image_context=image_context
    )
    
    return response.full_text_annotation
```

**Telugu Script Handling**:
- Unicode range: U+0C00 to U+0C7F
- Supports all Telugu characters, vowels, consonants, and diacritics
- Handles conjunct consonants (e.g., క్ష, త్ర)
- Preserves virama (halant) for proper rendering

### 7.3 LLM Normalization for Multilingual Text

**Strategy**: Use LLM to normalize Telugu medical terms to English equivalents

```python
TELUGU_NORMALIZATION_PROMPT = """You are a medical terminology translator. Translate Telugu medical terms to standard English medical terminology.

Input (Telugu): రోగికి మధుమేహం ఉంది. మెట్‌ఫార్మిన్ 500mg రోజుకు రెండుసార్లు.

Output (English): Patient has diabetes. Metformin 500mg twice daily.

Rules:
1. Translate medical conditions to standard English terms
2. Keep medication names in English (they are often transliterated)
3. Preserve dosages and frequencies
4. Maintain clinical accuracy

Now translate:
{telugu_text}
"""

async def normalize_telugu_text(telugu_text: str) -> str:
    """Normalize Telugu medical text to English."""
    from langchain.llms import OpenAI
    from langchain.prompts import PromptTemplate
    
    llm = OpenAI(temperature=0)  # Deterministic output
    prompt = PromptTemplate(
        template=TELUGU_NORMALIZATION_PROMPT,
        input_variables=["telugu_text"]
    )
    
    chain = prompt | llm
    normalized_text = await chain.ainvoke({"telugu_text": telugu_text})
    
    return normalized_text
```

**Telugu Medical Terminology Dictionary**:

```python
TELUGU_MEDICAL_TERMS = {
    # Common conditions
    "మధుమేహం": "diabetes",
    "రక్తపోటు": "hypertension",
    "జ్వరం": "fever",
    "దగ్గు": "cough",
    "తలనొప్పి": "headache",
    "కడుపునొప్పి": "abdominal pain",
    
    # Body parts
    "గుండె": "heart",
    "కాలేయం": "liver",
    "మూత్రపిండాలు": "kidneys",
    "ఊపిరితిత్తులు": "lungs",
    
    # Medications (transliterated)
    "మెట్‌ఫార్మిన్": "metformin",
    "పారాసిటమాల్": "paracetamol",
    "ఇన్సులిన్": "insulin",
    
    # Procedures
    "రక్త పరీక్ష": "blood test",
    "ఎక్స్-రే": "x-ray",
    "స్కాన్": "scan",
}

def translate_telugu_term(telugu_term: str) -> Optional[str]:
    """Translate Telugu medical term to English."""
    return TELUGU_MEDICAL_TERMS.get(telugu_term.strip())
```

### 7.4 Code-Switching Handling

**Code-switching**: Mixing English and Telugu within same sentence

Example: "రోగికి Type 2 Diabetes ఉంది"
(Patient has Type 2 Diabetes)

**Handling Strategy**:
1. Detect language at sentence level
2. Extract English medical terms even from Telugu sentences
3. Use bilingual NER (Named Entity Recognition)
4. Preserve English terms during translation

```python
import re

def extract_english_terms(mixed_text: str) -> List[str]:
    """Extract English terms from mixed Telugu-English text."""
    # English words are typically in ASCII range
    english_pattern = r'[A-Za-z][A-Za-z0-9\s]*'
    english_terms = re.findall(english_pattern, mixed_text)
    
    # Filter out single characters and common words
    filtered_terms = [
        term.strip() 
        for term in english_terms 
        if len(term.strip()) > 2
    ]
    
    return filtered_terms

def process_code_switched_text(text: str) -> Dict[str, Any]:
    """Process text with code-switching."""
    # Extract English medical terms
    english_terms = extract_english_terms(text)
    
    # Detect primary language
    lang, conf = detect_language(text)
    
    if lang == 'te':
        # Translate Telugu portions, preserve English terms
        telugu_portions = remove_english_terms(text)
        translated = translate_telugu_text(telugu_portions)
        
        # Merge back English terms
        result = merge_translations(translated, english_terms)
    else:
        result = text
    
    return {
        "original": text,
        "normalized": result,
        "detected_language": lang,
        "english_terms": english_terms
    }
```



## 8. API Design

### 8.1 RESTful API Endpoints

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: API Key in header (`X-API-Key: <key>`)

#### 8.1.1 Document Management

**Upload Document**
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
X-API-Key: <api_key>

Parameters:
- file: binary (required) - Document file (JPEG, PNG, PDF)
- patient_id: string (required) - Patient identifier
- document_type: string (optional) - Type of document
- language_hint: string (optional) - Language hint (en, te, mixed)

Response 202 Accepted:
{
  "document_id": "DOC-uuid-...",
  "status": "processing",
  "message": "Document uploaded successfully and queued for processing",
  "estimated_completion_time": "2024-01-15T10:32:00Z"
}

Response 400 Bad Request:
{
  "error": "validation_error",
  "message": "File size exceeds 10MB limit",
  "details": {...}
}
```

**Check Processing Status**
```http
GET /api/v1/documents/{document_id}/status
X-API-Key: <api_key>

Response 200 OK:
{
  "document_id": "DOC-uuid-...",
  "status": "completed",  // uploaded | processing | completed | failed
  "patient_id": "P123456",
  "events_extracted": 3,
  "fraud_signals_detected": 1,
  "processing_time_ms": 135000,
  "completed_at": "2024-01-15T10:32:15Z"
}

Response 404 Not Found:
{
  "error": "not_found",
  "message": "Document not found"
}
```

#### 8.1.2 Timeline Queries

**Get Patient Timeline**
```http
GET /api/v1/patients/{patient_id}/timeline
X-API-Key: <api_key>

Query Parameters:
- start_date: string (optional) - ISO 8601 date (YYYY-MM-DD)
- end_date: string (optional) - ISO 8601 date (YYYY-MM-DD)
- event_types: string (optional) - Comma-separated list (diagnosis,medication,procedure)
- limit: integer (optional, default=100) - Max events to return
- offset: integer (optional, default=0) - Pagination offset

Response 200 OK:
{
  "patient_id": "P123456",
  "patient_name": "రాజు కుమార్",
  "timeline": [
    {
      "date": "2024-01-15",
      "date_precision": "day",
      "confidence": 0.95,
      "events": [
        {
          "event_id": "EVT-001",
          "event_type": "diagnosis",
          "diagnosis_name": "Type 2 Diabetes Mellitus",
          "diagnosis_code": "E11",
          "provider": "Dr. వెంకట రావు",
          "clinic": "రాజు క్లినిక్",
          "confidence": 0.95,
          "document_id": "DOC-uuid-..."
        }
      ]
    }
  ],
  "pagination": {
    "total_count": 25,
    "limit": 100,
    "offset": 0,
    "has_more": false
  },
  "summary": {
    "total_events": 25,
    "date_range": {
      "earliest": "2023-06-10",
      "latest": "2024-01-15"
    },
    "event_type_counts": {
      "diagnosis": 8,
      "medication": 12,
      "procedure": 3,
      "lab_result": 2
    }
  }
}

Response 404 Not Found:
{
  "error": "not_found",
  "message": "Patient not found"
}
```

#### 8.1.3 Fraud Detection

**Get Fraud Signals**
```http
GET /api/v1/patients/{patient_id}/fraud
X-API-Key: <api_key>

Query Parameters:
- severity: string (optional) - Filter by severity (low,medium,high,critical)
- fraud_type: string (optional) - Filter by type (duplicate_event,cost_outlier,temporal_anomaly)
- reviewed: boolean (optional) - Filter by review status

Response 200 OK:
{
  "patient_id": "P123456",
  "fraud_signals": [
    {
      "signal_id": "FS-uuid-...",
      "fraud_type": "duplicate_event",
      "severity": "high",
      "confidence": 0.92,
      "description": "Duplicate diagnosis detected within 7 days",
      "related_events": ["EVT-001", "EVT-002"],
      "metadata": {
        "similarity_score": 0.95,
        "time_difference_days": 3,
        "same_provider": false
      },
      "detected_at": "2024-01-15T10:32:20Z",
      "reviewed": false
    }
  ],
  "summary": {
    "total_signals": 5,
    "by_severity": {
      "critical": 0,
      "high": 2,
      "medium": 2,
      "low": 1
    },
    "by_type": {
      "duplicate_event": 2,
      "cost_outlier": 2,
      "temporal_anomaly": 1
    },
    "unreviewed_count": 5
  }
}
```

#### 8.1.4 Health Check

**System Health**
```http
GET /api/v1/health
X-API-Key: <api_key>

Response 200 OK:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "api": "healthy",
    "mongodb": "healthy",
    "redis": "healthy",
    "worker": "healthy"
  },
  "version": "1.0.0"
}

Response 503 Service Unavailable:
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "api": "healthy",
    "mongodb": "unhealthy",
    "redis": "healthy",
    "worker": "degraded"
  },
  "errors": [
    "MongoDB connection timeout"
  ]
}
```

### 8.2 Request/Response Models (Pydantic)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

class DocumentUploadRequest(BaseModel):
    patient_id: str = Field(..., min_length=1, max_length=100)
    document_type: Optional[Literal["prescription", "lab_report", "discharge_summary", "other"]] = None
    language_hint: Optional[Literal["en", "te", "mixed"]] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: Literal["processing"]
    message: str
    estimated_completion_time: datetime

class TimelineQueryRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[Literal["diagnosis", "medication", "procedure", "lab_result"]]] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    
    @validator('end_date')
    def end_date_after_start_date(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class TimelineEvent(BaseModel):
    event_id: str
    event_type: str
    event_date: datetime
    confidence: float
    # Additional fields based on event_type

class TimelineEntry(BaseModel):
    date: str  # ISO 8601 date
    date_precision: str
    confidence: float
    events: List[TimelineEvent]

class TimelineResponse(BaseModel):
    patient_id: str
    patient_name: str
    timeline: List[TimelineEntry]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]

class FraudSignalResponse(BaseModel):
    signal_id: str
    fraud_type: str
    severity: str
    confidence: float
    description: str
    related_events: List[str]
    metadata: Dict[str, Any]
    detected_at: datetime
    reviewed: bool

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

### 8.3 API Versioning Strategy

**URL-based versioning**: `/api/v1/`, `/api/v2/`

**Version Support Policy**:
- Current version (v1): Fully supported
- Previous version: Deprecated with 6-month sunset period
- Breaking changes require new major version

**Deprecation Headers**:
```http
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: </api/v2/docs>; rel="successor-version"
```



## 9. Docker Deployment Architecture

### 9.1 Docker Compose Configuration

```yaml
version: '3.8'

services:
  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: bharat-health-api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - OCR_PROVIDER=google_vision
      - GOOGLE_VISION_API_KEY=${GOOGLE_VISION_API_KEY}
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./documents:/app/documents
      - ./logs:/app/logs
    depends_on:
      - mongodb
      - redis
    networks:
      - bharat-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Celery Worker for Document Processing
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: bharat-health-worker
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - OCR_PROVIDER=google_vision
      - GOOGLE_VISION_API_KEY=${GOOGLE_VISION_API_KEY}
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./documents:/app/documents
      - ./logs:/app/logs
    depends_on:
      - mongodb
      - redis
    networks:
      - bharat-net
    restart: unless-stopped
    command: celery -A app.tasks worker --loglevel=info --concurrency=2

  # MongoDB Database
  mongodb:
    image: mongo:7.0
    container_name: bharat-health-mongodb
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
      - MONGO_INITDB_DATABASE=bharat_health
    volumes:
      - mongodb-data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - bharat-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache & Queue
  redis:
    image: redis:7.2-alpine
    container_name: bharat-health-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - bharat-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  mongodb-data:
    driver: local
  redis-data:
    driver: local

networks:
  bharat-net:
    driver: bridge
```

### 9.2 Dockerfile Configurations

**Dockerfile.api** (FastAPI Application):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY ./config /app/config

# Create directories
RUN mkdir -p /app/documents /app/logs

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Dockerfile.worker** (Celery Worker):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app
COPY ./config /app/config

# Create directories
RUN mkdir -p /app/documents /app/logs

# Run Celery worker
CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info", "--concurrency=2"]
```

### 9.3 Enviro