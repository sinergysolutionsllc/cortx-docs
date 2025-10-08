"""
Analytics API Router

Provides endpoints for hybrid mode comparison analytics and training dashboard.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.policy_router import PolicyRouter
from cortx_core.logging import logger
from fastapi import APIRouter, Header, HTTPException, Query

router = APIRouter()

# This will be injected by the main app
policy_router: PolicyRouter = None


def get_policy_router() -> PolicyRouter:
    """Dependency to get policy router instance"""
    if policy_router is None:
        raise HTTPException(status_code=503, detail="Policy router not initialized")
    return policy_router


@router.get("/comparison/summary")
async def get_comparison_summary(
    domain: str | None = Query(None, description="Filter by domain"),
    days_back: int = Query(30, description="Number of days to include"),
    x_tenant_id: str = Header(default="default"),
) -> dict[str, Any]:
    """
    Get high-level comparison statistics between JSON and RAG validation.

    Used for the training dashboard overview.
    """
    try:
        # In production, this would query actual comparison data from database
        # For now, return mock data that demonstrates the structure

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        summary = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back,
            },
            "overall_metrics": {
                "total_comparisons": 1250,
                "avg_agreement_rate": 0.78,
                "json_only_failures": 185,
                "rag_only_failures": 142,
                "common_failures": 923,
                "avg_rag_confidence": 0.84,
                "comparison_trend": "improving",  # improving, declining, stable
            },
            "domain_breakdown": [
                {
                    "domain": "gtas",
                    "comparisons": 850,
                    "agreement_rate": 0.82,
                    "avg_rag_confidence": 0.87,
                    "top_disagreement_categories": [
                        "TAS_VALIDATION",
                        "DATE_FORMATTING",
                        "AMOUNT_PRECISION",
                    ],
                },
                {
                    "domain": "grants",
                    "comparisons": 250,
                    "agreement_rate": 0.71,
                    "avg_rag_confidence": 0.79,
                    "top_disagreement_categories": ["ELIGIBILITY_RULES", "COMPLIANCE_CHECKS"],
                },
                {
                    "domain": "claims",
                    "comparisons": 150,
                    "agreement_rate": 0.68,
                    "avg_rag_confidence": 0.82,
                    "top_disagreement_categories": ["MEDICAL_CODING", "COVERAGE_RULES"],
                },
            ],
            "confidence_distribution": {
                "high_confidence": {"range": "0.9-1.0", "count": 425, "agreement_rate": 0.95},
                "medium_confidence": {"range": "0.7-0.9", "count": 620, "agreement_rate": 0.78},
                "low_confidence": {"range": "0.0-0.7", "count": 205, "agreement_rate": 0.52},
            },
        }

        logger.info(f"Generated comparison summary for domain='{domain}', days_back={days_back}")

        return summary

    except Exception as e:
        logger.error(f"Failed to generate comparison summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get comparison data: {str(e)}"
        ) from e


@router.get("/comparison/detailed")
async def get_detailed_comparison(
    domain: str = Query(..., description="Domain to analyze"),
    rule_category: str | None = Query(None, description="Filter by rule category"),
    confidence_min: float = Query(0.0, description="Minimum confidence filter"),
    limit: int = Query(100, description="Maximum number of comparisons to return"),
    x_tenant_id: str = Header(default="default"),
) -> dict[str, Any]:
    """
    Get detailed comparison data for specific domain and filters.

    Used for drill-down analysis in the training dashboard.
    """
    try:
        # Mock detailed comparison data
        detailed_comparisons = []

        for i in range(min(limit, 25)):  # Generate sample data
            comparison = {
                "comparison_id": f"comp_{uuid.uuid4().hex[:8]}",
                "timestamp": (datetime.utcnow() - timedelta(minutes=i * 5)).isoformat(),
                "domain": domain,
                "rule_category": rule_category
                or ["TAS_VALIDATION", "DATE_FORMATTING", "AMOUNT_PRECISION"][i % 3],
                "json_failures": [
                    {"rule_id": f"JSON_{j:03d}", "severity": "error"} for j in range((i % 3) + 1)
                ],
                "rag_failures": [
                    {
                        "rule_id": f"RAG_{j:03d}",
                        "severity": "error",
                        "confidence": 0.75 + (i % 20) * 0.01,
                    }
                    for j in range((i % 4) + 1)
                ],
                "agreement_metrics": {
                    "json_only_count": (i % 2),
                    "rag_only_count": (i % 3),
                    "common_count": min(len([]), len([])),  # Would calculate overlap
                    "agreement_rate": 0.6 + (i % 40) * 0.01,
                    "avg_rag_confidence": 0.7 + (i % 30) * 0.01,
                },
                "discrepancies": (
                    [
                        {
                            "type": "json_missed",
                            "rule_id": f"MISSED_{i:03d}",
                            "description": "JSON validation missed pattern detected by RAG",
                            "rag_confidence": 0.8 + (i % 20) * 0.01,
                        }
                    ]
                    if i % 3 == 0
                    else []
                ),
            }
            detailed_comparisons.append(comparison)

        result = {
            "domain": domain,
            "rule_category": rule_category,
            "filters": {"confidence_min": confidence_min, "limit": limit},
            "total_found": len(detailed_comparisons),
            "comparisons": detailed_comparisons,
            "summary_stats": {
                "avg_agreement_rate": sum(
                    c["agreement_metrics"]["agreement_rate"] for c in detailed_comparisons
                )
                / len(detailed_comparisons),
                "avg_rag_confidence": sum(
                    c["agreement_metrics"]["avg_rag_confidence"] for c in detailed_comparisons
                )
                / len(detailed_comparisons),
                "total_discrepancies": sum(len(c["discrepancies"]) for c in detailed_comparisons),
            },
        }

        logger.info(
            f"Generated detailed comparison for domain='{domain}', rule_category='{rule_category}'"
        )

        return result

    except Exception as e:
        logger.error(f"Failed to generate detailed comparison: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get detailed comparison: {str(e)}"
        ) from e


@router.get("/comparison/trends")
async def get_comparison_trends(
    domain: str | None = Query(None, description="Filter by domain"),
    metric: str = Query(
        "agreement_rate", description="Metric to trend: agreement_rate, confidence, accuracy"
    ),
    period: str = Query("daily", description="Period: hourly, daily, weekly"),
    days_back: int = Query(30, description="Number of days to include"),
    x_tenant_id: str = Header(default="default"),
) -> dict[str, Any]:
    """
    Get time-series trends for comparison metrics.

    Used for trend analysis in the training dashboard.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Generate mock trend data
        data_points = []
        current_date = start_date

        while current_date <= end_date:
            # Mock trending data with some variation
            base_value = 0.75
            variation = (hash(current_date.isoformat()) % 100) / 500  # Random-like variation

            data_point = {
                "timestamp": current_date.isoformat(),
                "value": base_value + variation,
                "sample_size": 50 + (hash(current_date.isoformat()) % 50),
            }

            data_points.append(data_point)

            if period == "hourly":
                current_date += timedelta(hours=1)
            elif period == "daily":
                current_date += timedelta(days=1)
            elif period == "weekly":
                current_date += timedelta(weeks=1)

        result = {
            "domain": domain,
            "metric": metric,
            "period": period,
            "time_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_back,
            },
            "data_points": data_points,
            "statistics": {
                "min_value": min(dp["value"] for dp in data_points),
                "max_value": max(dp["value"] for dp in data_points),
                "avg_value": sum(dp["value"] for dp in data_points) / len(data_points),
                "trend_direction": "improving",  # Would calculate actual trend
            },
        }

        logger.info(
            f"Generated trend data for metric='{metric}', period='{period}', days_back={days_back}"
        )

        return result

    except Exception as e:
        logger.error(f"Failed to generate trend data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trend data: {str(e)}") from e


@router.get("/comparison/rules/{rule_id}")
async def get_rule_comparison_analysis(
    rule_id: str,
    days_back: int = Query(30, description="Number of days to analyze"),
    x_tenant_id: str = Header(default="default"),
) -> dict[str, Any]:
    """
    Get detailed analysis for a specific rule's JSON vs RAG performance.

    Used for rule-specific analysis in the training dashboard.
    """
    try:
        # Mock rule-specific analysis
        analysis = {
            "rule_id": rule_id,
            "rule_name": f"Rule {rule_id} - Validation Analysis",
            "analysis_period": {
                "start_date": (datetime.utcnow() - timedelta(days=days_back)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days_back,
            },
            "performance_comparison": {
                "total_validations": 245,
                "json_detected": 180,
                "rag_detected": 165,
                "both_detected": 142,
                "agreement_rate": 0.79,
                "json_only_detections": 38,
                "rag_only_detections": 23,
            },
            "confidence_analysis": {
                "rag_confidence_distribution": {
                    "high": {"range": "0.9+", "count": 85, "accuracy": 0.95},
                    "medium": {"range": "0.7-0.9", "count": 60, "accuracy": 0.82},
                    "low": {"range": "<0.7", "count": 20, "accuracy": 0.65},
                },
                "avg_confidence": 0.86,
                "confidence_trend": "stable",
            },
            "discrepancy_patterns": [
                {
                    "pattern": "Edge case handling",
                    "frequency": 15,
                    "description": "RAG misses edge cases that JSON catches",
                    "examples": ["Null values in required fields", "Boundary value validations"],
                },
                {
                    "pattern": "Context sensitivity",
                    "frequency": 12,
                    "description": "RAG catches contextual issues JSON misses",
                    "examples": ["Business logic violations", "Cross-field dependencies"],
                },
            ],
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Improve RAG training data for edge cases",
                    "expected_impact": "Reduce false negatives by ~20%",
                },
                {
                    "priority": "medium",
                    "action": "Add contextual examples to JSON rule documentation",
                    "expected_impact": "Better rule understanding and maintenance",
                },
            ],
        }

        logger.info(f"Generated rule analysis for rule_id='{rule_id}'")

        return analysis

    except Exception as e:
        logger.error(f"Failed to generate rule analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rule analysis: {str(e)}") from e


@router.get("/health")
async def analytics_health_check() -> dict[str, Any]:
    """Health check for analytics endpoints"""
    return {
        "status": "healthy",
        "service": "cortx-analytics",
        "endpoints": [
            "/comparison/summary",
            "/comparison/detailed",
            "/comparison/trends",
            "/comparison/rules/{rule_id}",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
