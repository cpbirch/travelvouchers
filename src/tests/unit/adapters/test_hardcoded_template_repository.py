"""Unit tests for HardcodedTemplateRepository adapter."""

import pytest


class TestHardcodedTemplateRepository:
    """Tests for HardcodedTemplateRepository driven port adapter."""

    def test_returns_skeleton_template_with_customer_placeholder(self) -> None:
        """find_by_id returns Template with {{customer.last_name}} placeholder."""
        from voucher_merger.adapters.hardcoded_template_repository import (
            HardcodedTemplateRepository,
        )
        from voucher_merger.ports.template_repository import Template

        repository = HardcodedTemplateRepository()

        result = repository.find_by_id("skeleton-template")

        assert result is not None
        assert isinstance(result, Template)
        assert result.template_id == "skeleton-template"
        assert "{{customer.last_name}}" in result.content

    def test_skeleton_template_contains_voucher_confirmation_text(self) -> None:
        """find_by_id returns Template with expected greeting and confirmation text."""
        from voucher_merger.adapters.hardcoded_template_repository import (
            HardcodedTemplateRepository,
        )

        repository = HardcodedTemplateRepository()

        result = repository.find_by_id("skeleton-template")

        assert result is not None
        assert "Dear" in result.content
        assert "voucher" in result.content.lower()

    @pytest.mark.parametrize(
        "unknown_template_id",
        [
            "unknown-template",
            "other-template",
            "",
            "SKELETON-TEMPLATE",  # Case sensitive
        ],
    )
    def test_returns_none_for_unknown_template_ids(
        self, unknown_template_id: str
    ) -> None:
        """find_by_id returns None for any template_id other than skeleton-template."""
        from voucher_merger.adapters.hardcoded_template_repository import (
            HardcodedTemplateRepository,
        )

        repository = HardcodedTemplateRepository()

        result = repository.find_by_id(unknown_template_id)

        assert result is None
