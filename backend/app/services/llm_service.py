"""
LLM service for structured medical information extraction using Gemini
"""
import json
import google.generativeai as genai
from app.config import settings
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LLMService:
    """Service for Gemini LLM operations"""
    
    def __init__(self):
        """Initialize Gemini client"""
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self._cached_candidates: list[str] | None = None
        self._cache_expires_at: datetime | None = None
        logger.info(f"Initialized LLM service with Gemini model: {self.model_name}")

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        if name.startswith("models/"):
            return name
        return f"models/{name}"

    def _resolve_model_candidates(self) -> list[str]:
        now = datetime.utcnow()
        if self._cached_candidates and self._cache_expires_at and now < self._cache_expires_at:
            return self._cached_candidates

        preferred = self._normalize_model_name(self.model_name)
        fallback_candidates = [
            preferred,
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.5-flash-lite",
            "models/gemini-flash-lite-latest",
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.0-flash",
        ]

        ordered_candidates = []
        for model_name in fallback_candidates:
            if model_name not in ordered_candidates:
                ordered_candidates.append(model_name)

        try:
            available = {
                m.name
                for m in genai.list_models()
                if "generateContent" in getattr(m, "supported_generation_methods", [])
            }
            matched = [m for m in ordered_candidates if m in available]
            if matched and matched[0] != preferred:
                logger.warning(
                    "Configured Gemini model '%s' unavailable. Falling back to '%s'.",
                    preferred,
                    matched[0],
                )
            if matched:
                self._cached_candidates = matched
                self._cache_expires_at = now + timedelta(minutes=10)
                return matched
        except Exception as e:
            logger.warning(f"Could not list Gemini models; using configured model directly: {e}")

        self._cached_candidates = ordered_candidates
        self._cache_expires_at = now + timedelta(minutes=10)
        return ordered_candidates

    @staticmethod
    def _is_model_selection_error(error_text: str) -> bool:
        normalized = error_text.lower()
        return (
            "not found" in normalized
            or "not supported" in normalized
            or "no longer available" in normalized
            or "unsupported" in normalized
        )
    
    def extract_structured_data(self, raw_text: str) -> Optional[Dict]:
        """
        Extract structured medical information from raw text using Gemini
        
        Args:
            raw_text: Raw text extracted from medical document
            
        Returns:
            Dictionary containing structured medical data, or None if extraction fails
        """
        try:
            logger.info("Starting LLM structured extraction with Gemini")
            
            # Construct the extraction prompt
            prompt = self._build_extraction_prompt(raw_text)
            
            response = None
            last_error: Optional[Exception] = None
            for candidate in self._resolve_model_candidates():
                try:
                    logger.info(f"Running structured extraction with Gemini model: {candidate}")
                    model = genai.GenerativeModel(candidate)

                    # Force JSON response via generation config if supported, otherwise rely on prompt rules.
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="application/json",
                            temperature=0.0,  # Deterministic output
                        )
                    )
                    break
                except Exception as model_error:
                    last_error = model_error
                    if self._is_model_selection_error(str(model_error)):
                        logger.warning(
                            "Gemini model '%s' failed due to availability; trying next candidate. Error: %s",
                            candidate,
                            model_error,
                        )
                        continue
                    raise

            if response is None:
                raise RuntimeError(f"All Gemini model candidates failed. Last error: {last_error}")
            
            # Parse response
            extracted_text = response.text
            
            logger.info(f"LLM extraction completed. Response length: {len(extracted_text)} chars")
            
            # Parse JSON from response
            json_text = self._extract_json_from_response(extracted_text)
            structured_data = json.loads(json_text)
            
            logger.info("Successfully parsed structured data from LLM response")
            return structured_data
            
        except Exception as e:
            error_msg = f"Gemini extraction failed: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Model: {self.model_name}")
            return None
    
    def _build_extraction_prompt(self, raw_text: str) -> str:
        """
        Build the extraction prompt with strict instructions
        
        Args:
            raw_text: Raw text from document
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a medical information extraction system. Extract structured data from the following medical document text.

STRICT RULES:
1. Return ONLY valid JSON, no commentary, no markdown formatting
2. Extract only the fields defined in the schema below
3. If a field is missing from the document, use null
4. Do NOT hallucinate or infer ICD codes - only include if explicitly stated
5. Do NOT assume chronic conditions - only mark chronic: true if explicitly stated
6. All dates MUST be in ISO format YYYY-MM-DD
7. All IDs (patient_id, encounter_id, claim_id) are REQUIRED - if missing, try to infer from document numbers/codes
8. If you cannot find required IDs, generate them in format: PATIENT_XXX, ENCOUNTER_XXX, CLAIM_XXX where XXX is derived from document

REQUIRED JSON SCHEMA:
{{
  "patient": {{
    "patient_id": "string (REQUIRED)",
    "name": "string or null",
    "dob": "YYYY-MM-DD or null",
    "gender": "M/F/Other or null",
    "insurance_policy_id": "string or null"
  }},
  "encounter": {{
    "encounter_id": "string (REQUIRED)",
    "admission_date": "YYYY-MM-DD or null",
    "discharge_date": "YYYY-MM-DD or null",
    "visit_type": "inpatient/outpatient/emergency or null",
    "department": "string or null"
  }},
  "claim": {{
    "claim_id": "string (REQUIRED)",
    "claim_amount": number or null,
    "approved_amount": number or null,
    "status": "submitted/approved/rejected/pending or null",
    "insurer_name": "string or null",
    "submission_date": "YYYY-MM-DD or null"
  }},
  "conditions": [
    {{
      "condition_name": "string (REQUIRED)",
      "icd_code": "string or null (only if explicitly stated)",
      "chronic": boolean or null (only true if explicitly stated as chronic)
    }}
  ],
  "hospital": {{
    "hospital_id": "string or null",
    "name": "string or null",
    "city": "string or null"
  }}
}}

DOCUMENT TEXT:
{raw_text}

Return ONLY the JSON object, nothing else:"""
        
        return prompt
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Extract JSON from LLM response, handling markdown code blocks
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Clean JSON string
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Remove ```json and ``` markers
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        elif text.startswith('```'):
            text = text[3:]  # Remove ```
        
        if text.endswith('```'):
            text = text[:-3]  # Remove trailing ```
        
        return text.strip()


# Global LLM service instance
llm_service = LLMService()
