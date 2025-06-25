"""This module contains the render context for the basic design."""

from django.core.exceptions import ObjectDoesNotExist

from nautobot_design_builder.errors import DesignValidationError
from nautobot_design_builder.context import Context, context_file

from nautobot.dcim.models import Location
from nautobot.extras.models import Status
from nautobot.ipam.models import Prefix

BRANCH_SUPERNET_PREFIXLEN = 21

@context_file("context.yaml")
class RackDesignContext(Context):
    """Render context for rack design."""

    def get_next_prefix(self):
        """Get next available prefix."""
        status = Status.objects.get(name="Active")
        base_prefix = Prefix.objects.get(prefix=self.base_prefix)
        available_prefixes = base_prefix.get_available_prefixes().iter_cidrs()
        filtered_available_prefixes = [p for p in available_prefixes if p.prefixlen <= BRANCH_SUPERNET_PREFIXLEN]
        try:
            container = sorted(filtered_available_prefixes, reverse=True, key=lambda x: x.prefixlen)[0]
            return str(container.network) + "/" + str(BRANCH_SUPERNET_PREFIXLEN) 
        except IndexError:
            raise DesignValidationError("Not enough IP space to create new branch!")
            

    @property
    def branch_supernet(self):
        """Calculate the branch prefixes."""
        try:
            location = Location.objects.get(name=self.site_name)
            return str(Prefix.objects.get(location=location, role__name="Branch:Supernet"))
        except ObjectDoesNotExist:
            return self.get_next_prefix()
