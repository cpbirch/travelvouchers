"""Domain service for validating template placeholders against known schema."""

from dataclasses import dataclass, field

from voucher_merger.domain.template import ExtractedPlaceholders


# Known placeholder schema - required and optional fields
KNOWN_CUSTOMER_PLACEHOLDERS = {
    "customer.first_name": {"required": True},
    "customer.last_name": {"required": True},
    "customer.title": {"required": False},
    "customer.email": {"required": False},
    "customer.phone": {"required": False},
}

KNOWN_SERVICE_PLACEHOLDERS = {
    "service.name": {"required": True},
    "service.provider": {"required": True},
    "service.pickup_time": {"required": False},
    "service.pickup_location": {"required": False},
    "service.dropoff_location": {"required": False},
    "service.passengers": {"required": False},
    "service.confirmation_code": {"required": False},
    "service.meeting_point": {"required": False},
    "service.tour_time": {"required": False},
    "service.duration": {"required": False},
    "service.notes": {"required": False},
}


@dataclass(frozen=True)
class ValidationResult:
    """Result of placeholder validation.

    Attributes:
        is_valid: True if validation passes (even with warnings).
        unknown_placeholders: Set of placeholders not in known schema.
        suggestions: Dict mapping unknown placeholders to suggested corrections.
        warnings: List of warning messages (e.g., optional field usage).
    """

    is_valid: bool
    unknown_placeholders: frozenset[str] = field(default_factory=frozenset)
    suggestions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings.

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        The minimum number of single-character edits needed to transform s1 into s2.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Calculate cost of insertions, deletions, substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class PlaceholderValidator:
    """Validates extracted placeholders against known schema.

    This service checks:
    - Unknown placeholders (not in schema) - generates warning
    - Typos in placeholder names - suggests corrections using Levenshtein distance
    - Optional field usage - generates warning about potential empty values
    """

    _MAX_SUGGESTION_EDIT_DISTANCE = 2

    def __init__(self) -> None:
        """Initialize validator with known schema."""
        self._known_placeholders = (
            set(KNOWN_CUSTOMER_PLACEHOLDERS.keys())
            | set(KNOWN_SERVICE_PLACEHOLDERS.keys())
        )

    def validate(self, extracted: ExtractedPlaceholders) -> ValidationResult:
        """Validate extracted placeholders against known schema.

        Args:
            extracted: Placeholders extracted from a template.

        Returns:
            ValidationResult with unknown placeholders, suggestions, and warnings.
        """
        unknown: set[str] = set()
        suggestions: dict[str, str] = {}
        warnings: list[str] = []

        # Validate customer placeholders
        for placeholder in extracted.customer_placeholders:
            if placeholder not in KNOWN_CUSTOMER_PLACEHOLDERS:
                unknown.add(placeholder)
                suggestion = self._find_suggestion(placeholder, "customer")
                if suggestion:
                    suggestions[placeholder] = suggestion
            else:
                # Check if optional field
                if not KNOWN_CUSTOMER_PLACEHOLDERS[placeholder]["required"]:
                    warnings.append(
                        f"{placeholder} is optional and may be empty"
                    )

        # Validate service placeholders
        for placeholder in extracted.service_placeholders:
            if placeholder not in KNOWN_SERVICE_PLACEHOLDERS:
                unknown.add(placeholder)
                suggestion = self._find_suggestion(placeholder, "service")
                if suggestion:
                    suggestions[placeholder] = suggestion
            else:
                # Check if optional field
                if not KNOWN_SERVICE_PLACEHOLDERS[placeholder]["required"]:
                    warnings.append(
                        f"{placeholder} is optional and may be empty"
                    )

        return ValidationResult(
            is_valid=True,  # Non-blocking validation - always valid
            unknown_placeholders=frozenset(unknown),
            suggestions=suggestions,
            warnings=warnings,
        )

    def _find_suggestion(self, placeholder: str, prefix: str) -> str | None:
        """Find the closest known placeholder using Levenshtein distance.

        Args:
            placeholder: The unknown placeholder.
            prefix: The expected prefix (customer or service).

        Returns:
            The closest known placeholder if within distance 2, else None.
        """
        if prefix == "customer":
            known = KNOWN_CUSTOMER_PLACEHOLDERS.keys()
        else:
            known = KNOWN_SERVICE_PLACEHOLDERS.keys()

        best_match = None
        best_distance = float("inf")

        for known_placeholder in known:
            distance = levenshtein_distance(placeholder, known_placeholder)
            if distance < best_distance:
                best_distance = distance
                best_match = known_placeholder

        # Only suggest if within reasonable edit distance
        if best_match and best_distance <= self._MAX_SUGGESTION_EDIT_DISTANCE:
            return best_match

        return None
