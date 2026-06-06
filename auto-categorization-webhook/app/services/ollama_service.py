"""
Ollama service for LLM-based ticket classification.
Supports llama3 (primary) and mistral (fallback) models.
"""
import json
import logging
import re
import httpx
import os
from typing import Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "llama3")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "mistral")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "5"))
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


class OllamaService:
    """Service for interacting with Ollama LLM API."""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.primary_model = PRIMARY_MODEL
        self.fallback_model = FALLBACK_MODEL
        self.timeout = OLLAMA_TIMEOUT

    async def is_available(self) -> bool:
        """Check if Ollama service is running."""
        if DEMO_MODE:
            return False  # Report unavailable in demo mode
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> list:
        """Get list of available models from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
        return []

    async def classify(self, prompt: str, model: Optional[str] = None) -> dict:
        """
        Send classification prompt to Ollama and parse JSON response.
        
        Args:
            prompt: The classification prompt
            model: Model to use (defaults to primary model)
            
        Returns:
            Parsed classification dict with category, subcategory, priority, confidence
        """
        model_to_use = model or self.primary_model
        logger.info(f"Calling Ollama with model: {model_to_use}")

        # If demo mode is enabled, skip Ollama and use mock classification
        if DEMO_MODE:
            logger.info("Demo mode enabled - using mock classification")
            return self._mock_classify(prompt)

        try:
            result = await self._call_ollama(prompt, model_to_use)
            return result
        except Exception as e:
            logger.warning(f"Primary model {model_to_use} failed: {e}. Trying fallback...")
            # Try fallback model
            try:
                result = await self._call_ollama(prompt, self.fallback_model)
                result["model_used"] = self.fallback_model
                return result
            except Exception as fallback_e:
                logger.error(f"Fallback model also failed: {fallback_e}. Using mock classification...")
                # Use mock classification for demonstration
                result = self._mock_classify(prompt)
                result["model_used"] = "mock"
                return result

    async def _call_ollama(self, prompt: str, model: str) -> dict:
        """Make the actual API call to Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent classification
                "top_p": 0.9,
                "num_predict": 300
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                raw_text = data.get("response", "")
                logger.debug(f"Raw Ollama response: {raw_text[:500]}")

                parsed = self._parse_json_response(raw_text)
                parsed["model_used"] = model
                return parsed
        except Exception as e:
            logger.warning(f"Ollama API call failed for model {model}: {e}")
            raise

    def _parse_json_response(self, text: str) -> dict:
        """
        Parse JSON from LLM response, handling various formats.
        LLMs sometimes wrap JSON in markdown or add extra text.
        """
        # Try direct JSON parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        match = re.search(code_block_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object pattern
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Last resort: build a default response
        logger.warning(f"Could not parse JSON from response: {text[:200]}")
        return self._build_default_response()

    def _build_default_response(self) -> dict:
        """Build a default fallback classification response."""
        return {
            "category": "General Inquiry",
            "subcategory": "Unclassified",
            "priority": "Medium",
            "confidence": 0.3,
            "reasoning": "Could not parse LLM response; using default classification"
        }

    def _mock_classify(self, prompt: str) -> dict:
        """
        Mock classification using keyword matching.
        Used for demonstration when Ollama is unavailable.
        """
        import re
        
        # Extract title and description from prompt - handle various line ending styles
        # Split by newlines to find Title: and Description: lines
        lines = prompt.split('\n')
        title = ""
        description = ""
        
        for i, line in enumerate(lines):
            if line.strip().startswith('Title:'):
                title = line.split(':', 1)[1].strip() if ':' in line else ""
            elif line.strip().startswith('Description:'):
                desc_start = line.split(':', 1)[1].strip() if ':' in line else ""
                # Capture description which might span multiple lines until "Respond with ONLY"
                desc_lines = [desc_start]
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('Respond with') or lines[j].strip().startswith('Previous') or lines[j].strip().startswith('Choose'):
                        break
                    if lines[j].strip():
                        desc_lines.append(lines[j].strip())
                description = " ".join(desc_lines)
        
        # If extraction failed, try a more aggressive approach
        if not title or not description:
            title_match = re.search(r'Title:\s*([^\n]+)', prompt)
            desc_match = re.search(r'Description:\s*([^\n]+(?:\n[^R][^\n]*)*)', prompt)
            
            if title_match:
                title = title_match.group(1).strip()
            if desc_match:
                description = desc_match.group(1).strip()
        
        searchable_text = f"{title} {description}".lower()
        
        # Keyword patterns for classification
        auth_keywords = ["login", "password", "authentication", "auth", "mfa", "sso", "access denied", "unauthorized", "reset", "unable to access", "cannot access"]
        billing_keywords = ["payment", "billing", "invoice", "refund", "subscription", "charge", "card", "not go through", "failed", "credit card"]
        tech_keywords = ["bug", "crash", "error", "technical", "performance", "slow", "api", "sync", "database", "crashes", "immediately", "launching", "app crashes"]
        network_keywords = ["vpn", "network", "connectivity", "internet", "connection", "latency", "bandwidth"]
        account_keywords = ["account", "profile", "update", "name", "email", "lockout", "permission", "access", "request"]
        
        category = "General Inquiry"
        subcategory = "Unclassified"
        priority = "Medium"
        confidence = 0.65
        
        # Count keyword matches for each category
        auth_score = sum(searchable_text.count(kw) for kw in auth_keywords)
        billing_score = sum(searchable_text.count(kw) for kw in billing_keywords)
        tech_score = sum(searchable_text.count(kw) for kw in tech_keywords)
        network_score = sum(searchable_text.count(kw) for kw in network_keywords)
        account_score = sum(searchable_text.count(kw) for kw in account_keywords)
        
        # Find the category with the highest score
        scores = {
            "Authentication": auth_score,
            "Billing": billing_score,
            "Technical": tech_score,
            "Network": network_score,
            "Account": account_score,
        }
        
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        # If a category has clear matches, use it
        if best_score > 0:
            category = best_category
            
            if category == "Authentication":
                subcategory = "Login Failure" if "login" in searchable_text else "Password Reset"
                confidence = 0.85
                priority = "High" if "cannot" in searchable_text or "unable" in searchable_text else "Medium"
            elif category == "Billing":
                subcategory = "Payment Failure" if "payment" in searchable_text or "charge" in searchable_text else "Invoice Issue"
                confidence = 0.82
                priority = "High" if "not" in searchable_text or "failed" in searchable_text else "Medium"
            elif category == "Technical":
                subcategory = "Bug Report" if "bug" in searchable_text or "crash" in searchable_text else "Performance Issue"
                confidence = 0.78
                priority = "Critical" if "crash" in searchable_text else "High" if "cannot" in searchable_text or "error" in searchable_text else "Medium"
            elif category == "Network":
                subcategory = "Connectivity" if "connect" in searchable_text or "vpn" in searchable_text else "Performance"
                confidence = 0.75
                priority = "High" if "cannot" in searchable_text else "Medium"
            elif category == "Account":
                subcategory = "Profile Update" if "profile" in searchable_text or "update" in searchable_text else "Access Request"
                confidence = 0.73
                priority = "Medium"
        
        return {
            "category": category,
            "subcategory": subcategory,
            "priority": priority,
            "confidence": confidence,
            "reasoning": f"Mock classification based on keyword matching (Ollama unavailable). Title: '{title[:50]}...', Extracted score: {best_score}"
        }


# Singleton instance
ollama_service = OllamaService()
