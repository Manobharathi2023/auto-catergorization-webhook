"""
Service for loading and managing few-shot training examples.
"""
import json
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

PACKAGE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)

FEW_SHOT_FILE = os.getenv(
    "FEW_SHOT_FILE",
    os.path.join(PACKAGE_ROOT, "data", "few_shot_examples.json")
)

DEFAULT_EXAMPLES = [
    {
        "title": "Cannot login after password reset",
        "category": "Authentication",
        "subcategory": "Login Failure",
        "priority": "High"
    },
    {
        "title": "Payment deducted twice",
        "category": "Billing",
        "subcategory": "Payment Failure",
        "priority": "High"
    },
    {
        "title": "System unavailable for all users",
        "category": "Technical",
        "subcategory": "Outage",
        "priority": "Critical"
    },
    {
        "title": "VPN connection keeps disconnecting",
        "category": "Network",
        "subcategory": "Connectivity",
        "priority": "Medium"
    },
    {
        "title": "Need access permission",
        "category": "Account",
        "subcategory": "Access Request",
        "priority": "Medium"
    }
]


class FewShotService:
    """Service to manage few-shot classification examples."""

    def __init__(self, file_path: str = FEW_SHOT_FILE):
        self.file_path = file_path
        self._examples: Optional[List[dict]] = None

    def load_examples(self) -> List[dict]:
        """Load examples from JSON file, with caching."""
        if self._examples is not None:
            return self._examples

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._examples = json.load(f)

            logger.info(
                f"Loaded {len(self._examples)} few-shot examples from {self.file_path}"
            )
            return self._examples

        except FileNotFoundError:
            logger.warning(
                f"Few-shot examples file not found. Using default examples."
            )
            self._examples = DEFAULT_EXAMPLES
            return self._examples

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing few-shot examples: {e}")
            self._examples = DEFAULT_EXAMPLES
            return self._examples

    def search_examples(self, query: str, max_results: int = 5) -> List[dict]:
        """
        Search for relevant examples based on keyword matching.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of matching examples
        """
        examples = self.load_examples()
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []

        for example in examples:
            score = 0

            text = (
                f"{example.get('title', '')} "
                f"{example.get('description', '')} "
                f"{example.get('category', '')} "
                f"{example.get('subcategory', '')}"
            ).lower()

            for term in query_terms:
                if term in text:
                    score += 1

                if term in example.get("category", "").lower():
                    score += 2

                if term in example.get("subcategory", "").lower():
                    score += 2

            if score > 0:
                scored.append((score, example))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [example for _, example in scored[:max_results]]

    def get_examples_by_category(self, category: str) -> List[dict]:
        """Get all examples for a specific category."""
        examples = self.load_examples()

        return [
            ex
            for ex in examples
            if ex.get("category", "").lower() == category.lower()
        ]

    def get_categories(self) -> List[str]:
        """Get all unique categories from examples."""
        examples = self.load_examples()

        return list(
            set(
                ex.get("category", "")
                for ex in examples
                if ex.get("category")
            )
        )


# Singleton instance
few_shot_service = FewShotService()