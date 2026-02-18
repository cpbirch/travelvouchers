"""Unit tests for placeholder validation.

Test Budget: 4 behaviors x 2 = 8 tests max
- Behavior 1: Detect unknown placeholders
- Behavior 2: Suggest corrections for typos (Levenshtein)
- Behavior 3: Warn about optional field usage
- Behavior 4: Pass validation for known placeholders

These tests exercise PlaceholderValidator through extracted placeholders,
which is the driving port entry point for validation.
"""

import pytest

from voucher_merger.domain.template import ExtractedPlaceholders


class TestPlaceholderValidator:
    """Tests for validating placeholders against known schema."""

    def test_detects_unknown_customer_placeholder(self) -> None:
        """Unknown customer placeholders are reported as unknown."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset({"customer.nickname"}),
            service_placeholders=frozenset(),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert "customer.nickname" in result.unknown_placeholders
        assert result.is_valid  # Still valid - warnings only

    def test_detects_unknown_service_placeholder(self) -> None:
        """Unknown service placeholders are reported as unknown."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset(),
            service_placeholders=frozenset({"service.custom_field"}),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert "service.custom_field" in result.unknown_placeholders

    def test_suggests_correction_for_typo_levenshtein_distance_one(self) -> None:
        """Typos with Levenshtein distance 1 get 'Did you mean' suggestions."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        # customer.lst_name is 1 edit away from customer.last_name
        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset({"customer.lst_name"}),
            service_placeholders=frozenset(),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert "customer.lst_name" in result.unknown_placeholders
        assert "customer.lst_name" in result.suggestions
        assert "customer.last_name" in result.suggestions["customer.lst_name"]

    def test_suggests_correction_for_typo_levenshtein_distance_two(self) -> None:
        """Typos with Levenshtein distance 2 also get suggestions."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        # customer.frist_name is 2 edits away from customer.first_name (transposition + r)
        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset({"customer.frist_name"}),
            service_placeholders=frozenset(),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert "customer.frist_name" in result.suggestions
        assert "customer.first_name" in result.suggestions["customer.frist_name"]

    def test_warns_about_optional_customer_field_usage(self) -> None:
        """Using optional customer fields generates a warning."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset({"customer.phone"}),
            service_placeholders=frozenset(),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert result.is_valid
        assert any("customer.phone" in w and "optional" in w.lower() for w in result.warnings)

    def test_warns_about_optional_service_field_usage(self) -> None:
        """Using optional service fields generates a warning."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset(),
            service_placeholders=frozenset({"service.pickup_time"}),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert result.is_valid
        assert any("service.pickup_time" in w and "optional" in w.lower() for w in result.warnings)

    def test_passes_validation_for_all_known_placeholders(self) -> None:
        """Valid placeholders pass without errors or warnings."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        extracted = ExtractedPlaceholders(
            customer_placeholders=frozenset({"customer.first_name", "customer.last_name"}),
            service_placeholders=frozenset({"service.name", "service.provider"}),
        )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert result.is_valid
        assert len(result.unknown_placeholders) == 0
        assert len(result.warnings) == 0  # Required fields don't warn

    @pytest.mark.parametrize(
        "placeholder,expected_suggestion",
        [
            ("customer.lst_name", "customer.last_name"),
            ("customer.fist_name", "customer.first_name"),
            ("service.nme", "service.name"),
            ("service.prvider", "service.provider"),
        ],
    )
    def test_suggests_corrections_for_various_typos(
        self,
        placeholder: str,
        expected_suggestion: str,
    ) -> None:
        """Various typos get correct suggestions based on Levenshtein distance."""
        from voucher_merger.domain.placeholder_validator import PlaceholderValidator

        prefix = placeholder.split(".")[0]
        if prefix == "customer":
            extracted = ExtractedPlaceholders(
                customer_placeholders=frozenset({placeholder}),
                service_placeholders=frozenset(),
            )
        else:
            extracted = ExtractedPlaceholders(
                customer_placeholders=frozenset(),
                service_placeholders=frozenset({placeholder}),
            )
        validator = PlaceholderValidator()

        result = validator.validate(extracted)

        assert placeholder in result.suggestions
        assert expected_suggestion in result.suggestions[placeholder]
