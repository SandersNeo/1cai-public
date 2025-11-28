# AI Issue Classifier Module

**Version:** 1.0  
**Status:**  Production Ready  
**Priority:** 2 (MEDIUM)

---

## Overview

AI Issue Classifier Module - intelligent classification of 1C issues with severity estimation and solution recommendations using AI/ML techniques.

---

## Features

### Issue Classifier
-  Classify issues by type (error, warning, performance, security, etc.)
-  Extract keywords and entities
-  Confidence scoring
-  Pattern matching
-  Batch classification

### Severity Estimator
-  Estimate severity (critical, high, medium, low, info)
-  Impact analysis
-  Urgency calculation
-  Score-based ranking (0-100)
-  Production impact detection

### Solution Recommender
-  Recommend solutions based on issue type
-  Knowledge base with solution templates
-  Success rate tracking
-  Quick fix identification
-  Step-by-step guidance

---

## Architecture

\\\
issue_classifier/
 domain/           # 4 domain models
    issue.py
    severity.py
    solution.py
 services/         # 3 services
    issue_classifier.py
    severity_estimator.py
    solution_recommender.py
 api/              # 4 REST endpoints
     classifier_routes.py
\\\

**Total:** 9 files, ~1,800 lines

---

## API Endpoints

- \POST /api/v1/issue-classifier/classify\ - Classify issue
- \POST /api/v1/issue-classifier/estimate-severity\ - Estimate severity
- \POST /api/v1/issue-classifier/recommend-solutions\ - Get solutions
- \POST /api/v1/issue-classifier/analyze-complete\ - Complete analysis

---

## Quick Start

### Classify Issue

\\\python
from issue_classifier.services import IssueClassifier
from issue_classifier.domain import Issue

classifier = IssueClassifier()

issue = Issue(
    issue_id="ISS-001",
    title="Database connection timeout",
    description="Users experiencing timeout errors when connecting to database"
)

classification = classifier.classify(issue)

print(f"Type: {classification.classified_type}")
print(f"Confidence: {classification.confidence}")
print(f"Keywords: {classification.keywords}")
\\\

### Estimate Severity

\\\python
from issue_classifier.services import SeverityEstimator
from issue_classifier.domain import SeverityFactors

estimator = SeverityEstimator()

factors = SeverityFactors(
    affects_production=True,
    affects_multiple_users=True,
    blocks_critical_function=True,
    has_workaround=False
)

severity = estimator.estimate_severity(classification, factors)

print(f"Severity: {severity.level}")
print(f"Score: {severity.score}")
print(f"Urgent: {severity.is_urgent}")
\\\

### Recommend Solutions

\\\python
from issue_classifier.services import SolutionRecommender

recommender = SolutionRecommender()

recommendations = recommender.recommend_solutions(classification)

print(f"Solutions: {len(recommendations.solutions)}")
print(f"Quick fix: {recommendations.has_quick_fix}")

if recommendations.best_solution:
    print(f"Best: {recommendations.best_solution.title}")
    print(f"Success rate: {recommendations.best_solution.success_rate}")
\\\

---

## REST API Examples

### Complete Analysis

\\\ash
curl -X POST "http://localhost:8000/api/v1/issue-classifier/analyze-complete" \\
  -H "Content-Type: application/json" \\
  -d '{
    "issue": {
      "issue_id": "ISS-001",
      "title": "Database timeout",
      "description": "Connection timeout errors"
    },
    "factors": {
      "affects_production": true,
      "affects_multiple_users": true
    }
  }'
\\\

---

## License

Part of 1C AI Stack - MIT License

---

**Created:** 2025-11-28  
**Maintainer:** 1C AI Stack Team
