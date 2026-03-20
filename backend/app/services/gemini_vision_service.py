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

    def _resolve_model_candidates(self) -> list[str]:
        """Resolve ordered generateContent model candidates for the active API key."""
        preferred = self._normalize_model_name(self.model_name)

        # Ordered fallbacks for broad compatibility across Gemini account tiers.
        fallback_candidates = [
            preferred,
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-2.5-flash-lite",
            "models/gemini-flash-lite-latest",
            "models/gemini-2.0-flash-lite",
            "models/gemini-2.0-flash",
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
            matched = [m for m in ordered_candidates if m in available]
            if matched and matched[0] != preferred:
                logger.warning(
                    "Configured Gemini model '%s' unavailable. Falling back to '%s'.",
                    preferred,
                    matched[0],
                )
            if matched:
                return matched
        except Exception as e:
            logger.warning(f"Could not list Gemini models; using configured model directly: {e}")

        # Last resort: try known candidates in configured order and let API errors guide fallback.
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
                
            prompt = (
                "You are an expert OCR and document understanding system. "
                "Extract all the text from this document accurately and preserving "
                "the layout, structure, and tabular data where possible."
            )

            last_error: Optional[Exception] = None
            model_candidates = self._resolve_model_candidates()
            response = None

            for candidate in model_candidates:
                try:
                    logger.info(f"Calling Gemini Vision model '{candidate}' for OCR")
                    model = genai.GenerativeModel(candidate)
                    response = model.generate_content([
                        prompt,
                        {
                            "mime_type": mime_type,
                            "data": file_bytes
                        }
                    ])
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
                raise RuntimeError(
                    f"All Gemini model candidates failed. Last error: {last_error}"
                )
            
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
