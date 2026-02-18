"""Unit tests for template placeholder extraction.

Test Budget: 3 behaviors x 2 = 6 tests max
- Behavior 1: Extract customer placeholders ({{customer.*}})
- Behavior 2: Extract service placeholders ({{service.*}})
- Behavior 3: Return placeholder list for validation

These tests exercise the TemplatePlaceholderExtractor through the Template
domain object, which is the entry point for placeholder extraction.
"""

import pytest


class TestTemplatePlaceholderExtractor:
    """Tests for extracting {{placeholder}} tokens from template content."""

    def test_extracts_customer_placeholders_from_template(self) -> None:
        """Extract all {{customer.*}} placeholders from template content."""
        from voucher_merger.domain.template import TemplatePlaceholderExtractor

        content = "<p>Dear {{customer.title}} {{customer.last_name}},</p>"
        extractor = TemplatePlaceholderExtractor()

        result = extractor.extract_placeholders(content)

        assert "customer.title" in result.customer_placeholders
        assert "customer.last_name" in result.customer_placeholders

    def test_extracts_service_placeholders_from_template(self) -> None:
        """Extract all {{service.*}} placeholders from template content."""
        from voucher_merger.domain.template import TemplatePlaceholderExtractor

        content = "<p>Service: {{service.name}} by {{service.provider}}</p>"
        extractor = TemplatePlaceholderExtractor()

        result = extractor.extract_placeholders(content)

        assert "service.name" in result.service_placeholders
        assert "service.provider" in result.service_placeholders

    def test_returns_all_placeholders_for_validation(self) -> None:
        """Return combined list of all placeholders for validation."""
        from voucher_merger.domain.template import TemplatePlaceholderExtractor

        content = "<p>Dear {{customer.first_name}}, your {{service.name}} is confirmed.</p>"
        extractor = TemplatePlaceholderExtractor()

        result = extractor.extract_placeholders(content)

        assert result.all_placeholders == {"customer.first_name", "service.name"}

    @pytest.mark.parametrize(
        "content,expected_customer,expected_service",
        [
            # Multiple customer placeholders
            (
                "<h1>{{customer.title}} {{customer.first_name}} {{customer.last_name}}</h1>",
                {"customer.title", "customer.first_name", "customer.last_name"},
                set(),
            ),
            # Multiple service placeholders
            (
                "<p>{{service.name}} | {{service.provider}} | {{service.pickup_time}}</p>",
                set(),
                {"service.name", "service.provider", "service.pickup_time"},
            ),
            # Empty content
            ("", set(), set()),
            # No placeholders
            ("<p>Plain text without placeholders</p>", set(), set()),
        ],
    )
    def test_extracts_placeholders_for_various_content_patterns(
        self,
        content: str,
        expected_customer: set,
        expected_service: set,
    ) -> None:
        """Placeholder extraction handles various content patterns correctly."""
        from voucher_merger.domain.template import TemplatePlaceholderExtractor

        extractor = TemplatePlaceholderExtractor()

        result = extractor.extract_placeholders(content)

        assert result.customer_placeholders == expected_customer
        assert result.service_placeholders == expected_service

    def test_handles_duplicate_placeholders(self) -> None:
        """Duplicate placeholders appear only once in result."""
        from voucher_merger.domain.template import TemplatePlaceholderExtractor

        content = "<p>{{customer.name}} loves {{customer.name}}</p>"
        extractor = TemplatePlaceholderExtractor()

        result = extractor.extract_placeholders(content)

        assert result.customer_placeholders == {"customer.name"}
        assert len(result.customer_placeholders) == 1
