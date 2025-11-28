"""Solution Recommender Service."""

from ..domain import (
    IssueClassification,
    IssueType,
    Solution,
    SolutionRecommendation,
    SolutionType,
)


class SolutionRecommender:
    """Service for recommending solutions to issues."""

    def __init__(self):
        """Initialize with solution knowledge base."""
        self.solution_templates = {
            IssueType.ERROR: [
                Solution(
                    solution_id="err_restart",
                    title="Restart Service",
                    description="Restart the affected service to clear error state",
                    solution_type=SolutionType.FIX,
                    steps=[
                        "Stop the service",
                        "Clear cache if applicable",
                        "Start the service",
                        "Verify functionality",
                    ],
                    estimated_time_minutes=10,
                    success_rate=0.7,
                    requires_restart=True,
                ),
                Solution(
                    solution_id="err_logs",
                    title="Check Error Logs",
                    description="Review detailed error logs for root cause",
                    solution_type=SolutionType.DOCUMENTATION,
                    steps=[
                        "Locate error logs",
                        "Search for error code/message",
                        "Identify root cause",
                        "Apply specific fix",
                    ],
                    estimated_time_minutes=20,
                    success_rate=0.9,
                ),
            ],
            IssueType.PERFORMANCE: [
                Solution(
                    solution_id="perf_cache",
                    title="Increase Cache Size",
                    description="Increase cache allocation to improve performance",
                    solution_type=SolutionType.CONFIGURATION,
                    steps=[
                        "Calculate optimal cache size",
                        "Update configuration",
                        "Restart service",
                        "Monitor performance",
                    ],
                    estimated_time_minutes=15,
                    success_rate=0.8,
                    requires_restart=True,
                ),
                Solution(
                    solution_id="perf_index",
                    title="Add Database Index",
                    description="Add index to improve query performance",
                    solution_type=SolutionType.FIX,
                    steps=[
                        "Identify slow queries",
                        "Analyze query plans",
                        "Create appropriate indexes",
                        "Test performance",
                    ],
                    estimated_time_minutes=30,
                    success_rate=0.85,
                ),
            ],
            IssueType.SECURITY: [
                Solution(
                    solution_id="sec_patch",
                    title="Apply Security Patch",
                    description="Install latest security updates",
                    solution_type=SolutionType.UPGRADE,
                    steps=[
                        "Download security patch",
                        "Test in staging",
                        "Schedule maintenance window",
                        "Apply patch to production",
                    ],
                    estimated_time_minutes=60,
                    success_rate=0.95,
                    requires_downtime=True,
                )
            ],
            IssueType.CONFIGURATION: [
                Solution(
                    solution_id="cfg_reset",
                    title="Reset to Default Configuration",
                    description="Reset configuration to known good state",
                    solution_type=SolutionType.CONFIGURATION,
                    steps=[
                        "Backup current configuration",
                        "Load default configuration",
                        "Apply custom settings",
                        "Test functionality",
                    ],
                    estimated_time_minutes=20,
                    success_rate=0.75,
                    requires_restart=True,
                )
            ],
        }

    def recommend_solutions(
        self, classification: IssueClassification
    ) -> SolutionRecommendation:
        """
        Recommend solutions for classified issue.

        Args:
            classification: Issue classification

        Returns:
            Solution recommendations
        """
        # Get solutions for issue type
        solutions = self.solution_templates.get(
            classification.classified_type, []
        ).copy()

        # Sort by success rate
        solutions.sort(key=lambda s: s.success_rate, reverse=True)

        # Generate reasoning
        reasoning = []
        if solutions:
            reasoning.append(
                f"Found {len(solutions)} solutions for {classification.classified_type.value}"
            )
            reasoning.append(
                f"Best solution has {solutions[0].success_rate*100:.0f}% success rate"
            )
        else:
            reasoning.append("No specific solutions found")
            reasoning.append("Manual investigation required")

        return SolutionRecommendation(
            issue_id=classification.issue.issue_id,
            solutions=solutions,
            confidence=classification.confidence * 0.8,  # Reduce confidence
            reasoning=reasoning,
            similar_issues_count=0,  # TODO: Implement similar issue search
        )

    def add_solution_template(self, issue_type: IssueType, solution: Solution):
        """
        Add new solution template to knowledge base.

        Args:
            issue_type: Issue type
            solution: Solution template
        """
        if issue_type not in self.solution_templates:
            self.solution_templates[issue_type] = []

        self.solution_templates[issue_type].append(solution)
