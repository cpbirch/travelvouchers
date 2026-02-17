"""
Root conftest.py for acceptance tests.

This file is loaded before any test modules and provides shared fixtures
and configuration for all acceptance tests.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "walking_skeleton: marks tests as walking skeleton (run first)"
    )
    config.addinivalue_line(
        "markers", "skip: marks tests as not yet implemented"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle @skip tags in Gherkin.

    Scenarios tagged with @skip in feature files are marked as pytest.skip.
    This allows us to write scenarios before implementing them.
    """
    for item in items:
        # Check if the test has skip marker from Gherkin tags
        if hasattr(item, 'callspec') and 'scenario' in item.callspec.params:
            scenario = item.callspec.params['scenario']
            if hasattr(scenario, 'tags') and 'skip' in scenario.tags:
                item.add_marker(pytest.mark.skip(reason="Scenario marked @skip - not yet implemented"))


@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_templates_dir(test_fixtures_dir):
    """Path to test template fixtures."""
    return test_fixtures_dir / "templates"
