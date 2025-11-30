# [NEXUS IDENTITY] ID: -4905010853109920497 | DATE: 2025-11-19

"""
AI Agents for different roles
Специализированные AI агенты для разных ролей
"""

from src.ai.agents.ai_issue_classifier import AIIssueClassifier
from src.ai.agents.architect_agent_extended import ArchitectAgentExtended
from src.ai.agents.business_analyst_agent import BusinessAnalystAgent
from src.ai.agents.developer_agent_enhanced import DeveloperAgentEnhanced
from src.ai.agents.its_knowledge_integrator import ITSKnowledgeIntegrator
from src.ai.agents.onec_server_optimizer import OneCServerOptimizer
from src.ai.agents.performance_analyzer import PerformanceAnalyzer
from src.ai.agents.project_manager_agent import ProjectManagerAgent
from src.ai.agents.qa_engineer_agent import QAEngineerAgent
from src.integrations.onec.ras_monitor import RASMonitor

# New agents
from src.ai.agents.security_agent import SecurityAgent
from src.ai.agents.sql_optimizer import SQLOptimizer
from src.ai.agents.tech_log_analyzer import TechLogAnalyzer
from src.ai.agents.technology_selector import TechnologySelector

try:
    from src.ai.agents.technical_writer_agent_extended import (
        TechnicalWriterAgentExtended,
    )
except ImportError:
    TechnicalWriterAgentExtended = None

__all__ = [
    "BusinessAnalystAgent",
    "QAEngineerAgent",
    "ArchitectAgentExtended",
    "TechnologySelector",
    "PerformanceAnalyzer",
    "ITSKnowledgeIntegrator",
    "SQLOptimizer",
    "OneCServerOptimizer",
    "TechLogAnalyzer",
    "RASMonitor",
    "AIIssueClassifier",
    "SecurityAgent",
    "ProjectManagerAgent",
    "DeveloperAgentEnhanced",
]
