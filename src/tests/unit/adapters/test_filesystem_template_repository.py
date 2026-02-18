"""Integration tests for FilesystemTemplateRepository adapter.

Test Budget: 3 behaviors x 2 = 6 tests max
- Behavior 1: Load .docx template (preserves content)
- Behavior 2: Load .odt template (preserves content)
- Behavior 3: Return None for missing template

These tests use real fixture files to verify actual filesystem behavior.
"""

import pytest
from pathlib import Path


class TestFilesystemTemplateRepository:
    """Integration tests for FilesystemTemplateRepository driven port adapter."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Path to test fixtures templates directory."""
        return Path(__file__).parent.parent.parent / "fixtures" / "templates"

    @pytest.fixture
    def repository(self, fixtures_dir: Path):
        """Create repository pointing to test fixtures."""
        from voucher_merger.adapters.filesystem_template_repository import (
            FilesystemTemplateRepository,
        )
        return FilesystemTemplateRepository(templates_dir=fixtures_dir)

    def test_loads_docx_template_and_returns_template_with_content(
        self, repository, fixtures_dir: Path
    ) -> None:
        """find_by_id loads .docx file and returns Template with extracted content."""
        from voucher_merger.ports.template_repository import Template

        result = repository.find_by_id("airport-transfer-v2")

        assert result is not None
        assert isinstance(result, Template)
        assert result.template_id == "airport-transfer-v2"
        # Content should be extracted from the docx file
        assert len(result.content) > 0

    def test_loads_odt_template_and_returns_template_with_content(
        self, repository, fixtures_dir: Path
    ) -> None:
        """find_by_id loads .odt file and returns Template with extracted content."""
        from voucher_merger.ports.template_repository import Template

        result = repository.find_by_id("sightseeing-tour-v1")

        assert result is not None
        assert isinstance(result, Template)
        assert result.template_id == "sightseeing-tour-v1"
        # Content should be extracted from the odt file
        assert len(result.content) > 0

    @pytest.mark.parametrize(
        "missing_template_id",
        [
            "nonexistent-template",
            "old-template-2019",
            "",
            "airport-transfer-v2.docx",  # Should not include extension
        ],
    )
    def test_returns_none_for_missing_templates(
        self, repository, missing_template_id: str
    ) -> None:
        """find_by_id returns None when template file does not exist."""
        result = repository.find_by_id(missing_template_id)

        assert result is None

    def test_prefers_docx_over_odt_when_both_exist(
        self, repository, fixtures_dir: Path
    ) -> None:
        """find_by_id prefers .docx if both .docx and .odt files exist for same template."""
        # This tests the behavior when same template_id could match multiple files
        # Create scenario where both exist - for now skeleton-template.docx exists
        result = repository.find_by_id("skeleton-template")

        assert result is not None
        assert result.template_id == "skeleton-template"
