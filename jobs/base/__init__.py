"""Basic design demonstrates the capabilities of the Design Builder."""
from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.design_job import DesignJob
from .context import BaseDataContext

name = "GRNOG18"

class BaseData(DesignJob):
    """Load base data."""

    class Meta:
        """Metadata for the BaseData design."""

        name = "Base Data"
        description = "Load Nautobot base data."
        nautobot_version = ">=2"
        has_sensitive_variables = False
        design_file = "designs/0000_basedata.yaml.j2"
        context_class = BaseDataContext

register_jobs(BaseData)
