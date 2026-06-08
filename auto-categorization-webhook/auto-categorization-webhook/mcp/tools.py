"""
MCP Tool implementations for ticket knowledge search.
"""
import json
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

FEW_SHOT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "few_shot_examples.json"
)


class TicketKnowledgeTool:
    """
    MCP Tool: Ticket Knowledge Search
    
    Searches historical ticket examples to help with classification.
    Uses keyword scoring for relevance ranking.
    """

    def __init__(self, examples_file: str = FEW_SHOT_FILE):
        self.examples_file = examples_file
        self._examples: Optional[List[dict]] = None

    def _load_examples(self) -> List[dict]:
        """Load ticket examples from JSON file."""
        if self._examples is not None:
            return self._examples
        try:
            with open(self.examples_file, "r") as f:
                self._examples = json.load(f)
            return self._examples
        except FileNotFoundError:
            logger.error(f"Examples file not found: {self.examples_file}")
            return []

    def search_examples(self, query: str, max_results: int = 5) -> dict:
        """
        Search for ticket examples matching the query.
        
        Args:
            query: Search string
            max_results: Number of results to return
            
        Returns:
            Dict with matching examples and metadata
        """
        examples = self._load_examples()
        query_lower = query.lower()
        query_terms = query_lower.split()

        scored = []
        for example in examples:
            score = 0
            searchable = " ".join([
                example.get("title", ""),
                example.get("description", ""),
                example.get("category", ""),
                example.get("subcategory", ""),
            ]).lower()

            for term in query_terms:
                if term in searchable:
                    score += 1
                if term in example.get("category", "").lower():
                    score += 2
                if term in example.get("subcategory", "").lower():
                    score += 2
                if term in example.get("title", "").lower():
                    score += 1

            if score > 0:
                scored.append((score, example))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [ex for _, ex in scored[:max_results]]

        return {
            "query": query,
            "total_found": len(results),
            "examples": [
                {
                    "ticket_id": ex.get("ticket_id"),
                    "title": ex.get("title"),
                    "description": ex.get("description", "")[:200],
                    "category": ex.get("category"),
                    "subcategory": ex.get("subcategory"),
                    "priority": ex.get("priority"),
                }
                for ex in results
            ]
        }

    def get_category_examples(self, category: str) -> dict:
        """
        Get all examples for a specific category.
        
        Args:
            category: Category name to filter by
            
        Returns:
            Dict with examples for the given category
        """
        examples = self._load_examples()
        filtered = [
            ex for ex in examples
            if ex.get("category", "").lower() == category.lower()
        ]

        return {
            "category": category,
            "total_found": len(filtered),
            "examples": [
                {
                    "ticket_id": ex.get("ticket_id"),
                    "title": ex.get("title"),
                    "subcategory": ex.get("subcategory"),
                    "priority": ex.get("priority"),
                }
                for ex in filtered
            ]
        }
