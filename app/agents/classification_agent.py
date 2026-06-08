"""
AI Agent Loop for ticket classification.
Implements: classify -> evaluate confidence -> retry if needed -> return final result.
"""
import logging
import time
from typing import Optional
from datetime import datetime

from app.services.ollama_service import ollama_service
from app.services.few_shot_service import few_shot_service
from app.prompts.classification_prompts import (
    build_classification_prompt,
    build_retry_prompt,
    build_fallback_prompt
)

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = float(0.6)
MAX_ATTEMPTS = 3


class ClassificationAgent:
    """
    AI Agent that orchestrates the ticket classification workflow.
    
    Agent Loop:
    1. Receive ticket
    2. Build prompt with few-shot examples
    3. Call LLM for classification
    4. Evaluate confidence
    5. If confidence < threshold: retry with improved prompt (max 3 times)
    6. Return final classification with reasoning trail
    """

    def __init__(self):
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.max_attempts = MAX_ATTEMPTS

    async def classify_ticket(
        self,
        ticket_id: str,
        title: str,
        description: Optional[str] = None
    ) -> dict:
        """
        Main agent classification method with retry loop.
        
        Returns:
            dict with classification results, confidence, model used, timing, and reasoning
        """
        start_time = time.time()
        examples = few_shot_service.load_examples()
        reasoning_steps = []
        last_result = None
        model_used = "unknown"

        logger.info(f"[Agent] Starting classification for ticket: {ticket_id}")
        reasoning_steps.append(f"Step 1: Received ticket '{title}' - beginning classification")

        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"[Agent] Attempt {attempt}/{self.max_attempts}")
            reasoning_steps.append(f"Step {attempt + 1}: Classification attempt {attempt}")

            try:
                # Build appropriate prompt based on attempt number
                if attempt == 1:
                    prompt = build_classification_prompt(title, description or "", examples)
                    reasoning_steps.append(f"  -> Using few-shot classification prompt with {len(examples)} examples")
                elif attempt < self.max_attempts:
                    prompt = build_retry_prompt(title, description or "", examples, last_result or {})
                    reasoning_steps.append(f"  -> Using retry prompt (low confidence: {last_result.get('confidence', 0):.2f})")
                else:
                    # Final attempt: use simplified fallback prompt
                    prompt = build_fallback_prompt(title, description or "")
                    reasoning_steps.append("  -> Using fallback prompt (simplified classification)")

                # Call LLM
                result = await ollama_service.classify(prompt)
                model_used = result.get("model_used", "llama3")
                confidence = float(result.get("confidence", 0.5))

                logger.info(
                    f"[Agent] Attempt {attempt} result: "
                    f"category={result.get('category')}, confidence={confidence:.2f}"
                )
                reasoning_steps.append(
                    f"  -> Result: {result.get('category')}/{result.get('subcategory')} "
                    f"(confidence: {confidence:.2f})"
                )

                last_result = result

                # Check if confidence is acceptable
                if confidence >= self.confidence_threshold:
                    reasoning_steps.append(
                        f"Step {attempt + 2}: Confidence {confidence:.2f} >= threshold {self.confidence_threshold} - accepting result"
                    )
                    logger.info(f"[Agent] Acceptable confidence on attempt {attempt}. Done.")
                    break
                else:
                    reasoning_steps.append(
                        f"Step {attempt + 2}: Confidence {confidence:.2f} < threshold {self.confidence_threshold} - retrying"
                    )
                    logger.warning(
                        f"[Agent] Low confidence ({confidence:.2f}) on attempt {attempt}. "
                        f"{'Retrying...' if attempt < self.max_attempts else 'Max attempts reached.'}"
                    )

            except Exception as e:
                logger.error(f"[Agent] Error on attempt {attempt}: {e}")
                reasoning_steps.append(f"  -> Error: {str(e)}")
                if attempt == self.max_attempts:
                    # Use safe default if all attempts failed
                    last_result = {
                        "category": "General Inquiry",
                        "subcategory": "Unclassified",
                        "priority": "Medium",
                        "confidence": 0.3,
                        "reasoning": f"Classification failed after {self.max_attempts} attempts: {str(e)}"
                    }
                    model_used = "fallback"

        elapsed_ms = (time.time() - start_time) * 1000
        reasoning_steps.append(f"Final: Classification complete in {elapsed_ms:.0f}ms after {attempt} attempt(s)")

        final_result = last_result or {}

        return {
            "ticket_id": ticket_id,
            "category": final_result.get("category", "General Inquiry"),
            "subcategory": final_result.get("subcategory", "Unclassified"),
            "priority": final_result.get("priority", "Medium"),
            "confidence": float(final_result.get("confidence", 0.3)),
            "model_used": model_used,
            "processing_time_ms": round(elapsed_ms, 2),
            "timestamp": datetime.utcnow(),
            "attempts": attempt,
            "agent_reasoning": "\n".join(reasoning_steps),
        }


# Singleton instance
classification_agent = ClassificationAgent()
