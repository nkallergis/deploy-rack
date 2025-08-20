"""Basic design demonstrates the capabilities of the Design Builder."""
from nautobot.apps.jobs import register_jobs, StringVar, ObjectVar, BooleanVar

from nautobot.dcim.models import Location

from nautobot_design_builder.choices import DesignModeChoices
from nautobot_design_builder.contrib import ext
from nautobot_design_builder.design_job import DesignJob

from .context import RackDesignContext

class RackDesign(DesignJob):
    """A basic design for design builder."""

    region = ObjectVar(
        label="Site",
        description="Site for the new rack",
        model=Location,
    )
    site_name = StringVar(label="Rack Name", regex=r"\w{3}\d+")
    # lab_topology = BooleanVar(label="Containerlab topology?", default=False, description="Generate a digital twin for the design (containerlab).")

    class Meta:
        """Metadata describing this design job."""

        design_mode = DesignModeChoices.DEPLOYMENT
        name = "Deploy new rack with Design Builder"
        description = "Create a new rack."
        version = "1.0"
        docs = "A basic design to deploy a new rack."
        nautobot_version = ">=2"
        has_sensitive_variables = False
        extensions = [ext.CableConnectionExtension, ext.NextPrefixExtension]
        design_file = "designs/0001_rackdesign.yaml.j2"
        context_class = RackDesignContext

register_jobs(RackDesign)
