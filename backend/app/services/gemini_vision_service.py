"""
Gemini Vision service for document text extraction (Replacing AWS Textract)
"""
import google.generativeai as genai
from app.config import settings
from app.services.gcs_service import gcs_service
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """Service for Gemini Vision API operations"""
    
    def __init__(self):
        """Initialize Gemini client"""
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        if name.startswith("models/"):
            return name
        return f"models/{name}"

    def _resolve_model_name(self) -> str:
        """Resolve a usable generateContent model name for the active API key."""
        preferred = self._normalize_model_name(self.model_name)

        # Ordered fallbacks for broad compatibility across Gemini account tiers.
        fallback_candidates = [
            preferred,
            "models/gemini-2.0-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.5-flash",
            "models/gemini-2.0-flash-lite",
        ]

        # De-duplicate while preserving order.
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
            for model_name in ordered_candidates:
                if model_name in available:
                    if model_name != preferred:
                        logger.warning(
                            "Configured Gemini model '%s' unavailable. Falling back to '%s'.",
                            preferred,
                            model_name,
                        )
                    return model_name
        except Exception as e:
            logger.warning(f"Could not list Gemini models; using configured model directly: {e}")

        # Last resort: try the configured model name and let API return a clear error if invalid.
        return preferred
    
    def extract_text_from_gcs(self, gcs_key: str) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """
        Extract text from document in GCS using Gemini Vision
        
        Args:
            gcs_key: GCS blob name of the document
            
        Returns:
            Tuple of (extracted_text, confidence_score, error_message)
            - extracted_text: Combined text from the model response
            - confidence_score: Always None for Gemini (unlike Textract box-level confidence)
            - error_message: Error description if extraction failed
        """
        try:
            logger.info(f"Downloading file from GCS for Gemini OCR: {gcs_key}")
            file_bytes = gcs_service.download_file(gcs_key)
            
            if not file_bytes:
                return None, None, f"Failed to download {gcs_key} from GCS"
            
            # Determine mime_type
            mime_type = "application/pdf"
            if gcs_key.lower().endswith(('.png', '.jpeg', '.jpg')):
                # Fallback purely for safety, though API enforces PDF currently
                mime_type = "image/jpeg"
                
            resolved_model_name = self._resolve_model_name()
            logger.info(f"Calling Gemini Vision model '{resolved_model_name}' for OCR")
            model = genai.GenerativeModel(resolved_model_name)
            
            prompt = (
                "You are an expert OCR and document understanding system. "
                "Extract all the text from this document accurately and preserving "
                "the layout, structure, and tabular data where possible."
            )
            
            response = model.generate_content([
                prompt,
                {
                    "mime_type": mime_type,
                    "data": file_bytes
                }
            ])
            
            extracted_text = response.text
            
            logger.info(f"Gemini Vision extraction completed: {len(extracted_text)} characters.")
            
            # Return None for confidence because Gemini does not natively supply
            # a reliable bounding-box average confidence score like Textract.
            return extracted_text, None, None
            
        except Exception as e:
            error_msg = f"Gemini Vision extraction failed: {str(e)}"
            logger.error(error_msg)
            return None, None, error_msg


# Global Gemini Vision service instance
gemini_vision_service = GeminiVisionService()
