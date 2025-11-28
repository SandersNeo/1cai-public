"""
Prometheus Metrics for Council and Security

Additional metrics for LLM Council and poetic jailbreak detection.
"""

from prometheus_client import Counter, Histogram

# Council metrics
council_queries_total = Counter(
    "council_queries_total",
    "Total number of council queries",
    ["status"],  # success, error
)

council_latency_seconds = Histogram(
    "council_latency_seconds",
    "Council query latency in seconds",
    buckets=[1, 5, 10, 15, 20, 30, 45, 60],
)

council_cost_multiplier = Histogram(
    "council_cost_multiplier",
    "Council cost multiplier (number of models used)",
    buckets=[2, 3, 4, 5, 6, 7, 8, 10],
)

# Security metrics
poetic_detections_total = Counter(
    "poetic_detections_total",
    "Total number of poetic form detections",
    ["is_poetic"],  # true, false
)

jailbreak_attempts_blocked = Counter(
    "jailbreak_attempts_blocked",
    "Number of blocked jailbreak attempts",
    ["reason"],  # poetic_intent, dangerous_keywords, etc.
)

security_validation_latency_ms = Histogram(
    "security_validation_latency_ms",
    "Security validation latency in milliseconds",
    buckets=[10, 25, 50, 100, 200, 500, 1000],
)

false_positives_total = Counter(
    "security_false_positives_total",
    "Number of potential false positives in security validation",
)
