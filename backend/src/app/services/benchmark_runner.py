"""
Benchmark Runner for CredenceAI Iteration 0.5 (Sprint 59)

Executes searches on a pre-labeled "gold-standard" query dataset.
Computes precision-recall metrics and prints regression/performance reports.
"""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.services.search_index import SearchIndexClient

logger = logging.getLogger(__name__)

# Pre-labeled gold standard dataset mapping queries to expected target URLs
GOLD_STANDARD = [
    {
        "query": "open source search engines",
        "expected_urls": [
            "https://mocked-result.com",
            "https://github.com/searxng/searxng"
        ]
    },
    {
        "query": "Tesla competitor electric vehicles",
        "expected_urls": [
            "https://res1.com",
            "https://res2.com"
        ]
    }
]


class BenchmarkRunner:
    """
    Automated benchmark suite executing quality and precision-recall comparisons.
    """

    def __init__(self, db: Session):
        self.db = db
        self.search_index = SearchIndexClient()

    def run_benchmark(self, use_hybrid: bool = True) -> Dict[str, Any]:
        """
        Run searches for all queries in gold standard set, compute precision and recall.
        """
        results_report = []
        total_precision = 0.0
        total_recall = 0.0

        for case in GOLD_STANDARD:
            query = case["query"]
            expected = set(case["expected_urls"])

            # Execute search
            if use_hybrid:
                results = self.search_index.hybrid_search(query, db=self.db)
            else:
                results = self.search_index.search(query, db=self.db)

            retrieved_urls = [r.get("url") for r in results]
            retrieved_set = set(retrieved_urls[:10])  # Evaluate Top-10

            # Calculate precision & recall
            true_positives = expected.intersection(retrieved_set)
            
            precision = len(true_positives) / len(retrieved_set) if retrieved_set else 0.0
            recall = len(true_positives) / len(expected) if expected else 0.0

            total_precision += precision
            total_recall += recall

            results_report.append({
                "query": query,
                "expected_count": len(expected),
                "retrieved_count": len(retrieved_set),
                "precision": round(precision, 4),
                "recall": round(recall, 4)
            })

        n_cases = len(GOLD_STANDARD)
        avg_precision = total_precision / n_cases if n_cases else 0.0
        avg_recall = total_recall / n_cases if n_cases else 0.0

        report = {
            "summary": {
                "total_queries": n_cases,
                "average_precision": round(avg_precision, 4),
                "average_recall": round(avg_recall, 4),
                "search_type": "hybrid" if use_hybrid else "standard"
            },
            "details": results_report
        }

        logger.info(
            f"BENCHMARK_RUNNER  queries={n_cases}  "
            f"avg_precision={avg_precision:.4f}  avg_recall={avg_recall:.4f}"
        )
        return report
