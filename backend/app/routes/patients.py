"""
Patient routes for user registration and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.patient import Patient
from app.schemas import PatientCreate, PatientResponse
from app.services.auth_service import hash_password
from app.services.graph_service import graph_service
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient account
    
    Validates:
    - Email is unique and valid format
    - Username is unique
    - Password is at least 8 characters
    
    Returns created patient information (without password)
    """
    try:
        # Check if email already exists
        existing_patient = db.query(Patient).filter(Patient.email == patient_data.email).first()
        if existing_patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        existing_username = db.query(Patient).filter(Patient.username == patient_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new patient with hashed password
        patient_id = str(uuid.uuid4())
        new_patient = Patient(
            id=patient_id,
            name=patient_data.name,
            email=patient_data.email,
            username=patient_data.username,
            password_hash=hash_password(patient_data.password)
        )
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        logger.info(f"Created new patient: {new_patient.username} (ID: {new_patient.id})")
        return new_patient
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating patient: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient account"
        )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get patient information by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    return patient


@router.get("/{patient_id}/graph")
async def get_patient_graph(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get patient's medical graph data from Neo4j
    
    Returns nodes and relationships for visualization:
    - Patient node
    - Encounter nodes
    - Claim nodes
    - Condition nodes
    - Hospital nodes
    - All relationships between them
    """
    # Verify patient exists in PostgreSQL
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Query Neo4j for graph data
    if not graph_service.driver:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph database is unavailable"
        )
    
    try:
        with graph_service.driver.session() as session:
            # Query to get all nodes and relationships for a patient
            query = """
            MATCH path = (p:Patient {patient_id: $patient_id})-[*1..2]-(n)
            WITH p, collect(DISTINCT n) as nodes, collect(DISTINCT relationships(path)) as rels
            RETURN 
                p as patient_node,
                nodes,
                rels
            """
            
            result = session.run(query, patient_id=patient_id)
            record = result.single()
            
            if not record:
                return {
                    "nodes": [],
                    "relationships": [],
                    "message": "No graph data found for this patient"
                }
            
            # Extract and format nodes
            formatted_nodes = []
            formatted_relationships = []
            
            # Add patient node
            patient_node = dict(record["patient_node"])
            formatted_nodes.append({
                "id": patient_node.get("patient_id"),
                "label": "Patient",
                "properties": patient_node
            })
            
            # Add related nodes
            for node in record["nodes"]:
                node_dict = dict(node)
                node_labels = list(node.labels)
                node_id = (
                    node_dict.get("encounter_id") or
                    node_dict.get("claim_id") or
                    node_dict.get("condition_name") or
                    node_dict.get("name")  # For Hospital
                )
                
                formatted_nodes.append({
                    "id": node_id,
                    "label": node_labels[0] if node_labels else "Unknown",
                    "properties": node_dict
                })
            
            # Extract relationships from nested arrays
            for rel_array in record["rels"]:
                for rel in rel_array:
                    formatted_relationships.append({
                        "source": rel.start_node.get("patient_id") or rel.start_node.get("encounter_id") or rel.start_node.get("name"),
                        "target": rel.end_node.get("encounter_id") or rel.end_node.get("claim_id") or rel.end_node.get("condition_name") or rel.end_node.get("name"),
                        "type": rel.type
                    })
            
            return {
                "nodes": formatted_nodes,
                "relationships": formatted_relationships
            }
            
    except Exception as e:
        logger.error(f"Error fetching graph data for patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch graph data: {str(e)}"
        )
