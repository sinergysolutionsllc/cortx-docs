"""
Integration tests for Analytics API

Tests hybrid mode comparison analytics and training dashboard endpoints
"""

import pytest


@pytest.mark.integration
class TestComparisonSummary:
    """Test GET /analytics/comparison/summary endpoint"""

    def test_get_comparison_summary_default(self, client):
        """Test getting comparison summary with defaults"""
        response = client.get("/analytics/comparison/summary")

        assert response.status_code == 200
        data = response.json()

        assert "period" in data
        assert "overall_metrics" in data
        assert "domain_breakdown" in data
        assert "confidence_distribution" in data

        # Check overall metrics structure
        metrics = data["overall_metrics"]
        assert "total_comparisons" in metrics
        assert "avg_agreement_rate" in metrics
        assert "json_only_failures" in metrics
        assert "rag_only_failures" in metrics
        assert "common_failures" in metrics

    def test_get_comparison_summary_with_domain_filter(self, client):
        """Test getting comparison summary filtered by domain"""
        response = client.get("/analytics/comparison/summary", params={"domain": "gtas"})

        assert response.status_code == 200

    def test_get_comparison_summary_with_days_back(self, client):
        """Test getting comparison summary with custom days back"""
        response = client.get("/analytics/comparison/summary", params={"days_back": 7})

        assert response.status_code == 200
        data = response.json()
        assert data["period"]["days"] == 7

    def test_get_comparison_summary_with_tenant(self, client):
        """Test getting comparison summary with tenant header"""
        response = client.get(
            "/analytics/comparison/summary", headers={"x-tenant-id": "custom_tenant"}
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestDetailedComparison:
    """Test GET /analytics/comparison/detailed endpoint"""

    def test_get_detailed_comparison(self, client):
        """Test getting detailed comparison data"""
        response = client.get("/analytics/comparison/detailed", params={"domain": "test.domain"})

        assert response.status_code == 200
        data = response.json()

        assert data["domain"] == "test.domain"
        assert "comparisons" in data
        assert "summary_stats" in data
        assert "filters" in data

    def test_get_detailed_comparison_with_filters(self, client):
        """Test getting detailed comparison with filters"""
        response = client.get(
            "/analytics/comparison/detailed",
            params={
                "domain": "test.domain",
                "rule_category": "TAS_VALIDATION",
                "confidence_min": 0.8,
                "limit": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["filters"]["confidence_min"] == 0.8
        assert data["filters"]["limit"] == 50

    def test_get_detailed_comparison_validates_comparisons(self, client):
        """Test detailed comparison validates comparison structure"""
        response = client.get("/analytics/comparison/detailed", params={"domain": "test.domain"})

        assert response.status_code == 200
        data = response.json()

        if data["comparisons"]:
            comparison = data["comparisons"][0]
            assert "comparison_id" in comparison
            assert "timestamp" in comparison
            assert "domain" in comparison
            assert "json_failures" in comparison
            assert "rag_failures" in comparison
            assert "agreement_metrics" in comparison


@pytest.mark.integration
class TestComparisonTrends:
    """Test GET /analytics/comparison/trends endpoint"""

    def test_get_comparison_trends_default(self, client):
        """Test getting comparison trends with defaults"""
        response = client.get("/analytics/comparison/trends")

        assert response.status_code == 200
        data = response.json()

        assert "metric" in data
        assert "period" in data
        assert "time_range" in data
        assert "data_points" in data
        assert "statistics" in data

    def test_get_comparison_trends_daily(self, client):
        """Test getting daily comparison trends"""
        response = client.get(
            "/analytics/comparison/trends",
            params={"metric": "agreement_rate", "period": "daily", "days_back": 30},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["metric"] == "agreement_rate"
        assert data["period"] == "daily"

    def test_get_comparison_trends_hourly(self, client):
        """Test getting hourly comparison trends"""
        response = client.get(
            "/analytics/comparison/trends",
            params={"metric": "confidence", "period": "hourly", "days_back": 1},
        )

        assert response.status_code == 200

    def test_get_comparison_trends_weekly(self, client):
        """Test getting weekly comparison trends"""
        response = client.get(
            "/analytics/comparison/trends",
            params={"metric": "accuracy", "period": "weekly", "days_back": 90},
        )

        assert response.status_code == 200

    def test_get_comparison_trends_with_domain(self, client):
        """Test getting trends filtered by domain"""
        response = client.get(
            "/analytics/comparison/trends",
            params={"domain": "gtas", "metric": "agreement_rate", "period": "daily"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == "gtas"

    def test_get_comparison_trends_validates_data_points(self, client):
        """Test trends validates data point structure"""
        response = client.get("/analytics/comparison/trends")

        assert response.status_code == 200
        data = response.json()

        if data["data_points"]:
            point = data["data_points"][0]
            assert "timestamp" in point
            assert "value" in point
            assert "sample_size" in point


@pytest.mark.integration
class TestRuleComparisonAnalysis:
    """Test GET /analytics/comparison/rules/{rule_id} endpoint"""

    def test_get_rule_comparison_analysis(self, client):
        """Test getting rule-specific comparison analysis"""
        response = client.get("/analytics/comparison/rules/TEST_001")

        assert response.status_code == 200
        data = response.json()

        assert data["rule_id"] == "TEST_001"
        assert "rule_name" in data
        assert "analysis_period" in data
        assert "performance_comparison" in data
        assert "confidence_analysis" in data
        assert "discrepancy_patterns" in data
        assert "recommendations" in data

    def test_get_rule_comparison_analysis_with_days_back(self, client):
        """Test getting rule analysis with custom period"""
        response = client.get("/analytics/comparison/rules/TEST_001", params={"days_back": 60})

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_period"]["days"] == 60

    def test_get_rule_comparison_validates_performance(self, client):
        """Test rule analysis validates performance metrics"""
        response = client.get("/analytics/comparison/rules/TEST_001")

        assert response.status_code == 200
        data = response.json()

        perf = data["performance_comparison"]
        assert "total_validations" in perf
        assert "json_detected" in perf
        assert "rag_detected" in perf
        assert "both_detected" in perf
        assert "agreement_rate" in perf

    def test_get_rule_comparison_validates_confidence(self, client):
        """Test rule analysis validates confidence analysis"""
        response = client.get("/analytics/comparison/rules/TEST_001")

        assert response.status_code == 200
        data = response.json()

        conf = data["confidence_analysis"]
        assert "rag_confidence_distribution" in conf
        assert "avg_confidence" in conf
        assert "confidence_trend" in conf


@pytest.mark.integration
class TestAnalyticsHealthCheck:
    """Test GET /analytics/health endpoint"""

    def test_analytics_health_check(self, client):
        """Test analytics health check"""
        response = client.get("/analytics/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "cortx-analytics"
        assert "endpoints" in data
        assert "timestamp" in data
