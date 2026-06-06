"""
Service for loading and managing few-shot training examples.
"""
import json
import logging
import os
from typing import List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
FEW_SHOT_FILE = os.getenv(
    "FEW_SHOT_FILE",
    os.path.join(PACKAGE_ROOT, "data", "few_shot_examples.json")
)


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
            logger.info(f"Loaded {len(self._examples)} few-shot examples from {self.file_path}")
            return self._examples
        except FileNotFoundError:
            logger.error(f"Few-shot examples file not found: {self.file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing few-shot examples: {e}")
            return []

    def search_examples(self, query: str, max_results: int = 5) -> List[dict]:
        """
        Search for relevant examples based on keyword matching.
        Used by MCP tool for semantic search.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching example dicts
        """
        examples = self.load_examples()
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for example in examples:
            score = 0
            text = f"{example.get('title', '')} {example.get('description', '')} {example.get('category', '')} {example.get('subcategory', '')}".lower()

            for term in query_terms:
                if term in text:
                    score += 1
                # Boost score for category/subcategory matches
                if term in example.get('category', '').lower():
                    score += 2
                if term in example.get('subcategory', '').lower():
                    score += 2

            if score > 0:
                scored.append((score, example))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:max_results]]

    def get_examples_by_category(self, category: str) -> List[dict]:
        """Get all examples for a specific category."""
        examples = self.load_examples()
        return [ex for ex in examples if ex.get("category", "").lower() == category.lower()]

    def get_categories(self) -> List[str]:
        """Get all unique categories from examples."""
        examples = self.load_examples()
        return list(set(ex.get("category", "") for ex in examples if ex.get("category")))


# Singleton instance
few_shot_service = FewShotService()
