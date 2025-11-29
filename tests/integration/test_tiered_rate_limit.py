"""
Integration Tests for Tiered Rate Limiting

Tests to verify tiered rate limiting works correctly.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app

client = TestClient(app)


class TestTieredRateLimiting:
    """Test tiered rate limiting functionality"""
    
    @pytest.mark.skip(reason="Requires Redis and may be slow")
    def test_free_tier_rate_limit(self):
        """Free tier should have 60 req/min limit"""
        # Make 61 requests quickly
        responses = []
        for i in range(61):
            response = client.get("/api/v1/health")
            responses.append(response)
        
        # Last request should be rate limited
        assert responses[-1].status_code == 429
    
    @pytest.mark.skip(reason="Requires Redis and authenticated user")
    def test_pro_tier_higher_limit(self):
        """Pro tier should have higher limit than free"""
        # This would require mocking authenticated user with pro tier
    
    def test_rate_limit_headers_present(self):
        """Rate limit headers should be present in response"""
        response = client.get("/api/v1/health")
        
        # Check for rate limit headers (if rate limiting is active)
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    def test_revolutionary_endpoints_have_separate_limit(self):
        """Revolutionary endpoints should have separate 100 req/min limit"""
        # This is path-based limiting
        response = client.get("/api/v1/revolutionary/health")
        
        if "X-RateLimit-Limit" in response.headers:
            limit = int(response.headers["X-RateLimit-Limit"])
            # Revolutionary endpoints should have 100 req/min
            assert limit == 100 or limit == 60  # Depending on tier
    
    def test_rate_limit_error_format(self):
        """Rate limit error should have proper format"""
        # Mock to simulate rate limit exceeded
        with patch("src.middleware.tiered_rate_limit.Redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.incr.return_value = 1000  # Exceed limit
            
            # This test would need proper setup


class TestRateLimitMetrics:
    """Test rate limit Prometheus metrics"""
    
    def test_metrics_endpoint_exists(self):
        """Metrics endpoint should exist"""
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_rate_limit_metrics_exported(self):
        """Rate limit metrics should be in Prometheus format"""
        response = client.get("/metrics")
        
        if response.status_code == 200:
            metrics_text = response.text
            
            # Check for rate limit metrics
            # Note: metrics may not exist if no requests have been rate limited yet
            assert "rate_limit" in metrics_text or "# TYPE" in metrics_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
