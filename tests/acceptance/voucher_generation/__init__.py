"""
Voucher Generation Acceptance Tests

This package contains BDD acceptance tests for the Voucher Generation System.
Tests are organized by milestone and invoke the system through the REST API
(driving port) only.

Structure:
- walking_skeleton.feature: First scenarios to validate architecture
- milestone_1_validation.feature: Request validation (US-010)
- milestone_2_templates_and_merging.feature: Templates and data merging
- milestone_3_output_generation.feature: PDF/HTML generation and storage
- milestone_4_robustness.feature: Idempotency, validation, error handling
- steps/: Step definition implementations
"""
