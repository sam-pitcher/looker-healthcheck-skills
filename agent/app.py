"""
Looker Healthcheck Agent: Orchestrator integrating Skills, Looker Client, and Reporters.
"""

from .config import LookerConfig
from .tools.skills_loader import SkillsLoader
from .tools.looker_client import LookerClient
from .reporters.markdown_reporter import MarkdownReporter

class LookerHealthcheckAgent:
    def __init__(self):
        self.config = LookerConfig.load()
        self.skills_loader = SkillsLoader("looker-healthcheck")
        self.skill_data = self.skills_loader.load_skill()
        self.looker = LookerClient(self.config)

    def run_audit(self) -> str:
        """Execute diagnostic audit and return formatted markdown report."""
        print(f"🚀 Initializing {self.skill_data['name']} against {self.config['base_url']}...")
        
        # 1. Fetch KPIs
        kpi_fields = [
            "query_metrics.async_processing_average",
            "query_metrics.execute_main_query_average",
            "query_metrics.acquire_connection_average",
            "query_metrics.model_init_computed_average",
            "query_metrics.explore_init_average",
            "query_metrics.stream_to_cache_average",
            "query_metrics.postprocessing_average"
        ]
        kpi_res = self.looker.run_query("system__activity", "query_metrics", kpi_fields, limit="1")
        kpis = kpi_res[0] if kpi_res else {}

        # 2. Fetch Outliers
        outlier_fields = [
            "query.id",
            "user.name",
            "dashboard.title",
            "query.view",
            "query_metrics.async_processing",
            "query_metrics.execute_main_query"
        ]
        outliers = self.looker.run_query(
            "system__activity", "query_metrics", outlier_fields,
            sorts=["query_metrics.async_processing desc"],
            limit="5"
        )

        # 3. Fetch History
        history_fields = ["history.source", "history.status", "history.query_run_count"]
        history = self.looker.run_query("system__activity", "history", history_fields, limit="25")

        # 4. Generate Report
        report_md = MarkdownReporter.build(self.config["base_url"], kpis, outliers, history)
        return report_md
