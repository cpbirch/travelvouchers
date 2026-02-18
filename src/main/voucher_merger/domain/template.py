"""Domain template services for placeholder extraction."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedPlaceholders:
    """Result of placeholder extraction from template content.

    Attributes:
        customer_placeholders: Set of customer placeholders (e.g., {"customer.name"}).
        service_placeholders: Set of service placeholders (e.g., {"service.provider"}).
    """

    customer_placeholders: frozenset[str]
    service_placeholders: frozenset[str]

    @property
    def all_placeholders(self) -> set[str]:
        """Return combined set of all placeholders."""
        return set(self.customer_placeholders) | set(self.service_placeholders)


class TemplatePlaceholderExtractor:
    """Extracts {{placeholder}} tokens from template content.

    This service identifies all mustache-style placeholders in template content
    and categorizes them by prefix (customer, service).
    """

    _PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+\.\w+)\}\}")

    def extract_placeholders(self, content: str) -> ExtractedPlaceholders:
        """Extract all placeholders from template content.

        Args:
            content: Template content (HTML markup with placeholders).

        Returns:
            ExtractedPlaceholders containing categorized placeholder sets.
        """
        all_matches = self._PLACEHOLDER_PATTERN.findall(content)

        customer_placeholders = frozenset(
            match for match in all_matches if match.startswith("customer.")
        )
        service_placeholders = frozenset(
            match for match in all_matches if match.startswith("service.")
        )

        return ExtractedPlaceholders(
            customer_placeholders=customer_placeholders,
            service_placeholders=service_placeholders,
        )
