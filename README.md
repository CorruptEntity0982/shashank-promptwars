# 🏥 Lattice Dashboard

**Lattice** is an intelligent medical document processing system that extracts structured healthcare data from PDFs and builds a comprehensive knowledge graph for patient care analysis. The system uses AI-powered extraction (OpenAI GPT-4o) and graph database technology (Neo4j) to create interconnected healthcare records.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-16.1.6-black.svg)
![Neo4j](https://img.shields.io/badge/neo4j-5.15-green.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Knowledge Graph Structure](#-knowledge-graph-structure)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Capabilities
- 📄 **PDF Document Processing**: Upload and process medical documents (EOBs, claims, encounter summaries)
- 🤖 **AI-Powered Extraction**: OpenAI GPT-4o extracts structured data from unstructured PDFs
- 📊 **Knowledge Graph**: Neo4j graph database creates interconnected patient health records
- 🔄 **Real-time Processing**: Asynchronous document processing with status tracking
- 🎨 **Modern UI**: Dark-themed dashboard with interactive visualizations
- 📈 **Graph Visualization**: Interactive node-based visualization of patient relationships
- 🚀 **Demo Mode**: One-click demo upload with predefined patient data

### Advanced Features
- **Longitudinal Data Tracking**: Merges new data with existing patient records
- **Multi-entity Extraction**: Patients, encounters, claims, conditions, providers, hospitals
- **Relationship Mapping**: Tracks connections between all healthcare entities
- **Auto-refresh Polling**: Real-time status updates every 5 seconds
- **Terminal-style JSON Viewer**: Beautiful formatted data display

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Browser                           │
│                  (React + Next.js UI)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                       │
│              (Routes /api/* to Backend)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴──────────────┐
        ↓                               ↓
┌───────────────────┐         ┌──────────────────┐
│  FastAPI Backend  │         │  Next.js Server  │
│   (Port 3000)     │         │   (Port 8000)    │
└────────┬──────────┘         └──────────────────┘
         │
    ┌────┼────────────────────┐
    ↓    ↓                    ↓
┌────────┐  ┌────────┐   ┌────────┐
│Postgres│  │ Redis  │   │ Neo4j  │
│  (DB)  │  │(Queue) │   │(Graph) │
└────────┘  └───┬────┘   └────────┘
                ↓
        ┌───────────────┐
        │ Celery Worker │
        │ (Processing)  │
        └───────────────┘
```

### Data Flow

1. **Upload**: User uploads PDF → FastAPI stores in PostgreSQL
2. **Queue**: FastAPI enqueues processing task → Redis/Celery
3. **Extract**: Celery worker uses AWS Textract to extract text
4. **Process**: OpenAI GPT-4o extracts structured medical entities
5. **Store**: Structured data saved to PostgreSQL (JSONB)
6. **Graph**: Neo4j graph updated with entities and relationships
7. **Visualize**: Frontend displays data and interactive graph

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** (Python 3.11): High-performance async API framework
- **PostgreSQL 15**: Relational database for document metadata
- **Neo4j 5.15**: Graph database for healthcare knowledge graph
- **Redis**: Message broker for Celery task queue
- **Celery**: Distributed task queue for async processing
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management

### AI & Processing
- **OpenAI API** (GPT-4o): Large language model for data extraction
- **AWS Textract**: PDF text extraction service
- **Boto3**: AWS SDK for Python

### Frontend
- **Next.js 16.1.6**: React framework with server-side rendering
- **React 19.2.3**: UI component library
- **Tailwind CSS 4**: Utility-first CSS framework
- **TypeScript**: Type-safe JavaScript

### Infrastructure
- **Docker & Docker Compose**: Container orchestration
- **Nginx**: Reverse proxy and load balancer
- **Python 3.11-slim**: Backend container image
- **Node 20-alpine**: Frontend container image

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Git**
- **OpenAI API Key** (for GPT-4o access)
- **AWS Credentials** (for Textract - optional but recommended)

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **OS**: macOS, Linux, or Windows with WSL2

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Lattice
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Database Configuration
POSTGRES_USER=Lattice
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=Lattice

# Neo4j Configuration
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# AWS Configuration (Optional - for Textract)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Application Configuration
ENVIRONMENT=development
```

### 3. Build Docker Containers

```bash
docker compose build
```

This will build:
- Backend (FastAPI)
- Frontend (Next.js)
- Celery Worker
- PostgreSQL
- Neo4j
- Redis
- Nginx

---

## ⚙️ Configuration

### Backend Configuration

Edit `backend/app/config.py` to customize:

```python
DATABASE_URL = "postgresql://..."  # Auto-configured from .env
NEO4J_URI = "bolt://neo4j:7687"   # Neo4j connection
OPENAI_API_KEY = "sk-..."         # OpenAI API key
```

### Neo4j Configuration

Neo4j is accessible at:
- **Browser UI**: http://localhost:7474
- **Bolt Protocol**: bolt://localhost:7687
- **Username**: `neo4j`
- **Password**: From `.env` file

### Nginx Configuration

Edit `infra/nginx.conf` to customize:
- Port mappings
- Upload size limits (default: 100MB)
- Proxy timeout settings

---

## 🎯 Running the Application

### Start All Services

```bash
docker compose up -d
```

This starts all services in detached mode:
- ✅ PostgreSQL (port 5432)
- ✅ Neo4j (ports 7474, 7687)
- ✅ Redis (port 6379)
- ✅ Backend (port 3000)
- ✅ Frontend (port 8000)
- ✅ Celery Worker
- ✅ Nginx (port 80)

### Check Service Status

```bash
docker compose ps
```

Expected output:
```
NAME                    STATUS    PORTS
Lattice-backend      Up        0.0.0.0:3000->3000/tcp
Lattice-celery       Up        
Lattice-db           Up        0.0.0.0:5432->5432/tcp
Lattice-frontend     Up        0.0.0.0:8000->8000/tcp
Lattice-neo4j        Up        0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
Lattice-nginx        Up        0.0.0.0:80->80/tcp
Lattice-redis        Up        0.0.0.0:6379->6379/tcp
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f frontend
```

### Stop Services

```bash
docker compose down
```

### Stop and Remove Data

```bash
docker compose down -v  # Removes volumes (databases)
```

---

## 📘 Usage Guide

### Accessing the Application

1. **Main Dashboard**: http://localhost/
2. **API Documentation**: http://localhost:3000/docs
3. **Neo4j Browser**: http://localhost:7474

### Uploading Documents

#### Method 1: Regular Upload
1. Navigate to http://localhost/
2. Enter a **Patient ID** (UUID format recommended)
3. Select a **PDF file** (max 50MB)
4. Click **📤 Upload Document**
5. Monitor processing status in the table below

#### Method 2: Demo Upload
1. Navigate to http://localhost/
2. Select a **PDF file** in the Demo Upload section
3. Click **🚀 Demo Upload** (uses predefined patient ID)
4. No need to enter patient ID manually

### Viewing Results

#### Structured Data
1. Wait for document status to show **✓ Completed**
2. Click **📋 View Data** button
3. View beautifully formatted JSON with extracted entities

#### Knowledge Graph
1. Wait for document status to show **✓ Completed**
2. Click **🔮 View Graph** button
3. Explore interactive graph visualization:
   - **Patient** nodes (purple)
   - **Encounter** nodes (blue)
   - **Claim** nodes (green)
   - **Condition** nodes (red)
   - **Hospital** nodes (orange)
   - **Provider** nodes (yellow)

### Understanding Processing Status

| Status      | Icon | Meaning                               |
|-------------|------|---------------------------------------|
| Uploaded    | ↑    | Document received, queued             |
| Processing  | ⟳    | AI extraction in progress             |
| Completed   | ✓    | Successfully processed                |
| Failed      | ✗    | Error occurred (check error message)  |

---

## 🔌 API Documentation

### Interactive API Docs

FastAPI provides auto-generated interactive documentation:

- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc

### Key Endpoints

#### Upload Document
```bash
POST /documents/upload
Content-Type: multipart/form-data

Parameters:
- patient_id: string (UUID recommended)
- file: PDF file (max 50MB)

Response:
{
  "id": "doc-uuid",
  "patient_id": "patient-uuid",
  "file_name": "document.pdf",
  "status": "uploaded"
}
```

#### List Documents
```bash
GET /documents/

Response:
[
  {
    "id": "doc-uuid",
    "patient_id": "patient-uuid",
    "file_name": "document.pdf",
    "status": "completed",
    "structured_data": { ... },
    "created_at": "2026-03-03T10:00:00",
    "processed_at": "2026-03-03T10:02:30"
  }
]
```

#### Get Patient Graph
```bash
GET /patients/{patient_id}/graph

Response:
{
  "nodes": [
    {
      "id": "node-1",
      "label": "Patient",
      "properties": { ... }
    }
  ],
  "relationships": [
    {
      "source": "node-1",
      "target": "node-2",
      "type": "HAD_ENCOUNTER"
    }
  ]
}
```

#### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2026-03-03T10:00:00",
  "services": {
    "database": "connected",
    "neo4j": "connected",
    "redis": "connected"
  }
}
```

---

## 🕸️ Knowledge Graph Structure

### Node Types

```cypher
// Patient Node
(:Patient {
  id: "uuid",
  name: "John Doe",
  date_of_birth: "1980-01-01",
  gender: "Male"
})

// Encounter Node
(:Encounter {
  id: "uuid",
  date: "2026-03-01",
  type: "Outpatient",
  diagnosis: "Annual Checkup"
})

// Claim Node
(:Claim {
  id: "uuid",
  claim_number: "CLM123456",
  total_amount: 250.00,
  date_of_service: "2026-03-01"
})

// Condition Node
(:Condition {
  id: "uuid",
  code: "E11.9",
  description: "Type 2 diabetes mellitus",
  status: "active"
})

// Hospital Node
(:Hospital {
  id: "uuid",
  name: "General Hospital",
  address: "123 Main St"
})

// Provider Node
(:Provider {
  id: "uuid",
  name: "Dr. Smith",
  specialty: "Family Medicine",
  npi: "1234567890"
})
```

### Relationship Types

```cypher
(Patient)-[:HAD_ENCOUNTER]->(Encounter)
(Patient)-[:HAS_CONDITION]->(Condition)
(Encounter)-[:RESULTED_IN_CLAIM]->(Claim)
(Encounter)-[:AT_HOSPITAL]->(Hospital)
(Encounter)-[:TREATED_BY]->(Provider)
(Claim)-[:COVERS_CONDITION]->(Condition)
```

### Example Cypher Queries

```cypher
// Find all encounters for a patient
MATCH (p:Patient {id: $patient_id})-[:HAD_ENCOUNTER]->(e:Encounter)
RETURN e
ORDER BY e.date DESC

// Find all conditions for a patient
MATCH (p:Patient {id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
RETURN c

// Find patient's care network
MATCH (p:Patient {id: $patient_id})-[:HAD_ENCOUNTER]->(e:Encounter)
      -[:TREATED_BY]->(prov:Provider)
RETURN p, e, prov
```

---

## 📁 Project Structure

```
Lattice/
├── backend/                    # FastAPI Backend
│   ├── alembic/               # Database migrations
│   │   └── versions/          # Migration scripts
│   ├── app/
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── document.py    # Document model
│   │   │   └── patient.py     # Patient model
│   │   ├── routes/            # API endpoints
│   │   │   ├── documents.py   # Document routes
│   │   │   ├── patients.py    # Patient routes
│   │   │   └── health.py      # Health check
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── structured_document.py
│   │   ├── services/          # Business logic
│   │   │   ├── llm_service.py       # OpenAI integration
│   │   │   ├── textract_service.py  # AWS Textract
│   │   │   ├── graph_service.py     # Neo4j operations
│   │   │   ├── s3_service.py        # S3 operations
│   │   │   └── pdf_service.py       # PDF processing
│   │   ├── tasks/             # Celery tasks
│   │   │   └── document_tasks.py
│   │   ├── workflows/         # LangGraph workflows
│   │   │   └── medical_extraction_graph.py
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database setup
│   │   └── main.py            # FastAPI app
│   ├── alembic.ini            # Alembic config
│   ├── celery_worker.py       # Celery worker entry
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend Docker image
│
├── frontend/                   # Next.js Frontend
│   ├── app/
│   │   ├── components/        # React components
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── GraphVisualization.tsx
│   │   │   └── StructuredDataModal.tsx
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Main dashboard
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript config
│   ├── tailwind.config.ts     # Tailwind config
│   ├── next.config.ts         # Next.js config
│   └── Dockerfile             # Frontend Docker image
│
├── infra/
│   └── nginx.conf             # Nginx configuration
│
├── design-docs/               # Design documentation
│   ├── design.md
│   ├── pitch.md
│   └── requirements.md
│
├── docker-compose.yml         # Docker orchestration
├── .env                       # Environment variables
└── README.md                  # This file
```

---

## 🔧 Development

### Running Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3000
```

### Running Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

### Running Database Migrations

```bash
# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback migration
docker compose exec backend alembic downgrade -1
```

### Running Celery Worker Locally

```bash
cd backend
celery -A celery_worker worker --loglevel=info
```

### Accessing PostgreSQL

```bash
docker compose exec db psql -U Lattice -d Lattice
```

### Accessing Neo4j

```bash
# Via Browser
open http://localhost:7474

# Via Cypher Shell
docker compose exec neo4j cypher-shell -u neo4j -p <password>
```

---

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :80  # or :3000, :7474, etc.

# Kill the process or change ports in docker-compose.yml
```

#### Docker Build Fails
```bash
# Clear Docker cache and rebuild
docker compose down -v
docker system prune -a
docker compose build --no-cache
docker compose up -d
```

#### Frontend Not Loading
```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose up -d --build frontend
```

#### Celery Not Processing Tasks
```bash
# Check Celery logs
docker compose logs celery

# Restart Celery worker
docker compose restart celery
```

#### Neo4j Connection Error
```bash
# Check Neo4j status
docker compose logs neo4j

# Restart Neo4j
docker compose restart neo4j

# Wait 30 seconds for Neo4j to fully start
```

#### OpenAI API Errors
- Verify your API key in `.env`
- Check your OpenAI account has credits
- Ensure GPT-4o access is enabled

#### Database Migration Issues
```bash
# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d db
docker compose exec backend alembic upgrade head
```

### Debug Mode

Enable debug logging:

```bash
# Backend
docker compose exec backend bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

### Health Checks

```bash
# Check all services
curl http://localhost/api/health

# Check backend directly
curl http://localhost:3000/health

# Check frontend
curl http://localhost:8000
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Follow ESLint rules, use Prettier
- **Commits**: Use conventional commit messages

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o API
- **Neo4j** for graph database technology
- **FastAPI** for the excellent Python framework
- **Next.js** for the React framework
- **Tailwind CSS** for beautiful styling

---

## 📞 Support

For issues, questions, or suggestions:

- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with [Feature Request] tag
- 📧 **Email**: support@Lattice.example.com
- 💬 **Discussions**: Use GitHub Discussions

---

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ PDF document upload
- ✅ AI-powered extraction
- ✅ Neo4j knowledge graph
- ✅ Interactive visualizations
- ✅ Dark theme UI

### Phase 2 (Planned)
- 🔄 Multi-document batch processing
- 🔍 Advanced search and filtering
- 📊 Analytics dashboard
- 🔐 User authentication
- 👥 Multi-tenant support

### Phase 3 (Future)
- 🤖 Predictive analytics
- 📱 Mobile app
- 🌐 FHIR API integration
- 🔔 Real-time notifications
- 📈 Business intelligence reports

---

**Built with ❤️ for healthcare innovation**

Version: 1.0.0  
Last Updated: March 3, 2026
