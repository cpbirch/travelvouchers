"""Port interface for template loading."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Template:
    """Template value object returned by the repository.

    Attributes:
        template_id: Unique identifier for the template.
        content: The template content (markup/HTML with placeholders).
    """

    template_id: str
    content: str


class TemplateRepository(Protocol):
    """Driven port for loading voucher templates.

    This port defines the contract for retrieving templates by their
    identifier. Adapters implementing this port may load templates from
    various sources (filesystem, database, cloud storage, etc.).
    """

    def find_by_id(self, template_id: str) -> Template | None:
        """Find a template by its identifier.

        Args:
            template_id: Unique identifier for the template.

        Returns:
            The template if found, None otherwise.
        """
        ...
