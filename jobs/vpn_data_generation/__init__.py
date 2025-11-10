"""Data generation for VPN Models."""
from nautobot.apps.jobs import register_jobs
from nautobot_design_builder.design_job import DesignJob
from .context import VPNDataGenerationContext

class VPNDataGeneration(DesignJob):
    """Data generation for VPN Models."""

    class Meta:
        """Metadata for the VPNDataGeneration design."""

        name = "VPN Models Data Generation"
        description = "Generate VPN Models data."
        nautobot_version = ">=2"
        has_sensitive_variables = False
        design_file = "designs/0000_vpn_data_generation.yaml.j2"
        context_class = VPNDataGenerationContext

register_jobs(VPNDataGeneration)
