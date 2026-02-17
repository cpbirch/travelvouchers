"""Hardcoded template repository adapter for walking skeleton."""

from voucher_merger.ports.template_repository import Template


class HardcodedTemplateRepository:
    """Hardcoded implementation of TemplateRepository for walking skeleton.

    This adapter returns a fixed skeleton template for initial architecture
    validation. It will be replaced by a real filesystem-based adapter.
    """

    _SKELETON_TEMPLATE_ID = "skeleton-template"
    _SKELETON_CONTENT = "Dear {{customer.last_name}}, Your voucher is confirmed."

    def find_by_id(self, template_id: str) -> Template | None:
        """Find a template by its identifier.

        Args:
            template_id: Unique identifier for the template.

        Returns:
            The skeleton template if template_id is "skeleton-template",
            None otherwise.
        """
        if template_id == self._SKELETON_TEMPLATE_ID:
            return Template(
                template_id=self._SKELETON_TEMPLATE_ID,
                content=self._SKELETON_CONTENT,
            )
        return None
