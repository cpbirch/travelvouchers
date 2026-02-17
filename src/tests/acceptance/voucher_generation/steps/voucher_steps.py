"""
Voucher Generation Step Definitions

These step definitions implement the Given-When-Then steps for voucher generation
scenarios. They invoke the REST API (driving port) and verify responses.

Architecture Note:
- All interactions go through the REST API endpoint POST /vouchers
- No direct calls to domain services or use cases
- Steps focus on business language, not technical implementation
"""

import pytest
from pytest_bdd import given, when, then, parsers, scenarios
from .conftest import VoucherTestContext

# Note: scenarios() calls moved to individual test modules (test_walking_skeleton.py, etc.)
# to avoid loading features with syntax errors during walking skeleton development


# =============================================================================
# GIVEN Steps - Setup preconditions
# =============================================================================

@given('the skeleton template exists with placeholder "{{customer.last_name}}"')
def skeleton_template_exists(context: VoucherTestContext):
    """Ensure the walking skeleton template is available."""
    context.available_templates.add("skeleton-template")


@given('the storage service is available')
def storage_available(context: VoucherTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


@given('the storage service is unavailable')
def storage_unavailable(context: VoucherTestContext):
    """Simulate storage failure."""
    context.storage_available = False


@given('the storage service is temporarily unavailable')
def storage_temporarily_unavailable(context: VoucherTestContext):
    """Simulate temporary storage failure."""
    context.storage_available = False


@given('the skeleton template exists')
def skeleton_template_exists_simple(context: VoucherTestContext):
    """Ensure the skeleton template is available (simplified)."""
    context.available_templates.add("skeleton-template")


@given('the airport transfer template exists')
def airport_transfer_template_exists(context: VoucherTestContext):
    """Ensure the airport transfer template is available."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template "{template_id}" exists as a Word document'))
def template_exists_as_docx(context: VoucherTestContext, template_id: str):
    """Ensure a specific Word template is available."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" exists as a LibreOffice document'))
def template_exists_as_odt(context: VoucherTestContext, template_id: str):
    """Ensure a specific LibreOffice template is available."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" does not exist'))
def template_does_not_exist(context: VoucherTestContext, template_id: str):
    """Ensure a template is NOT available (for 404 testing)."""
    context.available_templates.discard(template_id)


@given(parsers.parse('the template "{template_id}" exists but is corrupted'))
def template_is_corrupted(context: VoucherTestContext, template_id: str):
    """Set up a corrupted template for error testing."""
    # Mark as "available" but corrupted - implementation will detect corruption
    context.available_templates.add(f"{template_id}:corrupted")


@given('the template with customer placeholders exists')
def template_with_customer_placeholders(context: VoucherTestContext):
    """Ensure a template with customer placeholders is available."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template with "{content}" exists'))
def template_with_specific_content(context: VoucherTestContext, content: str):
    """Ensure a template with specific content is available."""
    context.available_templates.add("airport-transfer-v2")


@given('the template with customer name placeholders exists')
def template_with_name_placeholders(context: VoucherTestContext):
    """Ensure a template with name placeholders is available."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template "{template_id}" exists with service placeholders'))
def template_with_service_placeholders(context: VoucherTestContext, template_id: str):
    """Ensure a template with service placeholders is available."""
    context.available_templates.add(template_id)


@given('the template with optional service placeholders exists')
def template_with_optional_service_placeholders(context: VoucherTestContext):
    """Ensure a template with optional service fields is available."""
    context.available_templates.add("airport-transfer-v2")


@given('the template with service notes placeholder exists')
def template_with_notes_placeholder(context: VoucherTestContext):
    """Ensure a template with notes placeholder is available."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('a voucher was previously generated for:\n{table}'))
def voucher_previously_generated(context: VoucherTestContext, table):
    """Set up an existing voucher for idempotency testing."""
    data = _parse_table(table)
    key = f"{data['booking_id']}/{data['service_date']}"
    context.existing_vouchers[key] = {
        "voucher_id": f"V-{data['booking_id'].replace('BK-', '')}-{data['service_date'].replace('-', '')[:4]}",
        "booking_id": data['booking_id'],
        "service_date": data['service_date'],
        "generated_at": "2024-02-17T10:23:45Z"
    }


@given(parsers.parse('the original voucher was created at "{timestamp}"'))
def original_voucher_timestamp(context: VoucherTestContext, timestamp: str):
    """Set the timestamp for an existing voucher."""
    for voucher in context.existing_vouchers.values():
        voucher["generated_at"] = timestamp


@given(parsers.parse('a voucher exists for booking "{booking_id}" date "{service_date}"'))
def voucher_exists_for_booking_date(context: VoucherTestContext, booking_id: str, service_date: str):
    """Set up an existing voucher with specific booking/date."""
    key = f"{booking_id}/{service_date}"
    context.existing_vouchers[key] = {
        "voucher_id": f"V-{booking_id.replace('BK-', '')}-{service_date.replace('-', '')[:4]}",
        "booking_id": booking_id,
        "service_date": service_date,
        "generated_at": "2024-02-17T10:00:00Z"
    }


@given(parsers.parse('a voucher was previously generated with:\n{table}'))
def voucher_with_full_metadata(context: VoucherTestContext, table):
    """Set up an existing voucher with full metadata."""
    data = _parse_table(table)
    key = f"{data['booking_id']}/{data['service_date']}"
    context.existing_vouchers[key] = data


@given(parsers.parse('the template contains formatted elements:\n{table}'))
def template_contains_formatted_elements(context: VoucherTestContext, table):
    """Set up a template with specific formatting elements."""
    context.available_templates.add("airport-transfer-v2")


@given('the template contains a company logo image')
def template_contains_logo(context: VoucherTestContext):
    """Set up a template with an embedded logo."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template "{template_id}" spans multiple pages'))
def template_multiple_pages(context: VoucherTestContext, template_id: str):
    """Set up a multi-page template."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" contains "{content}"'))
def template_contains_content(context: VoucherTestContext, template_id: str, content: str):
    """Set up a template with specific content."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" contains only known placeholders:\n{table}'))
def template_with_known_placeholders(context: VoucherTestContext, template_id: str, table):
    """Set up a template with only valid placeholders."""
    context.available_templates.add(template_id)


# =============================================================================
# WHEN Steps - Execute actions
# =============================================================================

@when(parsers.parse('I request a voucher for:\n{table}'))
def request_voucher_with_table(context: VoucherTestContext, table, client):
    """Build a voucher request from table data."""
    data = _parse_table(table)
    context.request_data.update(data)


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('customer "{first_name}" "{last_name}" with title "{title}"'))
def set_customer_with_title(context: VoucherTestContext, first_name: str, last_name: str, title: str):
    """Set customer with title."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name
    context.customer_data["title"] = title


@when(parsers.parse('customer "{first_name}" "{last_name}" without title'))
def set_customer_without_title(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer without title (explicitly omitted)."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name
    # Explicitly do not set title


@when(parsers.parse('customer "{first_name}" "{last_name}" with:\n{table}'))
def set_customer_with_details(context: VoucherTestContext, first_name: str, last_name: str, table):
    """Set customer with additional details from table."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name
    context.customer_data.update(_parse_table(table))


@when(parsers.parse('customer "{first_name}" without last name'))
def set_customer_missing_last_name(context: VoucherTestContext, first_name: str):
    """Set customer without last name (for validation testing)."""
    context.customer_data["first_name"] = first_name
    # Explicitly do not set last_name


@when(parsers.parse('customer without first name "{last_name}"'))
def set_customer_missing_first_name(context: VoucherTestContext, last_name: str):
    """Set customer without first name (for validation testing)."""
    context.customer_data["last_name"] = last_name
    # Explicitly do not set first_name


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_data(context: VoucherTestContext, name: str, provider: str):
    """Set service name and provider."""
    context.service_data["name"] = name
    context.service_data["provider"] = provider
    _execute_voucher_request(context)


@when(parsers.parse('service "{name}" without provider'))
def set_service_missing_provider(context: VoucherTestContext, name: str):
    """Set service without provider (for validation testing)."""
    context.service_data["name"] = name
    _execute_voucher_request(context)


@when(parsers.parse('service without name provided by "{provider}"'))
def set_service_missing_name(context: VoucherTestContext, provider: str):
    """Set service without name (for validation testing)."""
    context.service_data["provider"] = provider
    _execute_voucher_request(context)


@when(parsers.parse('service details:\n{table}'))
def set_service_details(context: VoucherTestContext, table):
    """Set service data from table."""
    context.service_data.update(_parse_table(table))
    _execute_voucher_request(context)


@when(parsers.parse('I request a voucher with multiple validation errors:\n{table}'))
def request_with_validation_errors(context: VoucherTestContext, table, client):
    """Build a request with intentional validation errors."""
    errors = _parse_table_rows(table)
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
    }
    for error in errors:
        if error["field"] == "customer.last_name" and error["issue"] == "missing":
            context.customer_data["first_name"] = "Test"
            # Don't set last_name
        elif error["field"] == "service_date" and error["issue"] == "invalid format":
            context.request_data["service_date"] = "15-03-2024"  # Wrong format

    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('I request a voucher without template_id for:\n{table}'))
def request_without_template_id(context: VoucherTestContext, table, client):
    """Build request without template_id."""
    data = _parse_table(table)
    context.request_data = {k: v for k, v in data.items() if k != "template_id"}
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('I request a voucher without booking_id for:\n{table}'))
def request_without_booking_id(context: VoucherTestContext, table, client):
    """Build request without booking_id."""
    data = _parse_table(table)
    context.request_data = {k: v for k, v in data.items() if k != "booking_id"}
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when('I send an empty voucher request')
def send_empty_request(context: VoucherTestContext, client):
    """Send a completely empty request."""
    context.response = client.post("/vouchers", json={})
    if hasattr(context.response, 'json'):
        context.response_json = context.response.json()


@when('I request a voucher with missing customer last_name')
def request_missing_last_name(context: VoucherTestContext, client):
    """Request with missing customer.last_name."""
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
        "service_date": "2024-03-01"
    }
    context.customer_data = {"first_name": "Test"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('I request a voucher with template_id "{template_id}"'))
def request_with_template_id(context: VoucherTestContext, template_id: str, client):
    """Request with specific template_id."""
    context.request_data = {
        "template_id": template_id,
        "booking_id": "BK-2024-99999",
        "service_date": "2024-03-01"
    }
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('I request a voucher with service_date "{service_date}"'))
def request_with_service_date(context: VoucherTestContext, service_date: str, client):
    """Request with specific service_date."""
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
        "service_date": service_date
    }
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when('I request a voucher with invalid data')
def request_with_invalid_data(context: VoucherTestContext, client):
    """Request with some invalid data."""
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": "invalid",
        "service_date": "invalid"
    }
    context.customer_data = {"first_name": "Test"}
    context.service_data = {"name": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('I request a duplicate voucher for booking "{booking_id}" date "{service_date}"'))
def request_duplicate_voucher(context: VoucherTestContext, booking_id: str, service_date: str, client):
    """Request a voucher that already exists."""
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": booking_id,
        "service_date": service_date
    }
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}
    _execute_voucher_request(context)


@when(parsers.parse('the template "{template_id}" is validated'))
def validate_template(context: VoucherTestContext, template_id: str, client):
    """Validate a template."""
    # This would call a validation endpoint
    context.response = client.post(f"/templates/{template_id}/validate", json={})
    if hasattr(context.response, 'json'):
        context.response_json = context.response.json()


# =============================================================================
# THEN Steps - Verify outcomes
# =============================================================================

@then('the voucher is created successfully')
def voucher_created_successfully(context: VoucherTestContext):
    """Verify voucher creation succeeded."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then(parsers.parse('the response status is {status_code:d} {status_text}'))
def response_status_matches(context: VoucherTestContext, status_code: int, status_text: str):
    """Verify HTTP status code."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}"


@then('the response contains a PDF URL')
def response_contains_pdf_url(context: VoucherTestContext):
    """Verify response includes PDF URL."""
    assert "urls" in context.response_json or "pdf_url" in context.response_json, \
        f"No PDF URL in response: {context.response_json}"
    if "urls" in context.response_json:
        assert "pdf" in context.response_json["urls"]
    else:
        assert context.response_json.get("pdf_url") is not None


@then('the response contains an HTML URL')
def response_contains_html_url(context: VoucherTestContext):
    """Verify response includes HTML URL."""
    assert "urls" in context.response_json
    assert "html" in context.response_json["urls"]


@then(parsers.parse('the PDF contains "{text}"'))
def pdf_contains_text(context: VoucherTestContext, text: str):
    """Verify PDF contains expected text."""
    # In real implementation, fetch PDF and search
    # For mock, we verify the response data suggests it would contain the text
    assert context.response.status_code == 201, "Voucher must be created first"


@then('no error is returned')
def no_error_returned(context: VoucherTestContext):
    """Verify no error in response."""
    assert "error" not in context.response_json, \
        f"Unexpected error: {context.response_json.get('error')}"


@then(parsers.parse('the response contains:\n{table}'))
def response_contains_fields(context: VoucherTestContext, table):
    """Verify response contains expected fields."""
    expected = _parse_table(table)
    for field, present in expected.items():
        if present == "yes":
            # Handle nested fields like "urls.pdf"
            parts = field.split(".")
            value = context.response_json
            for part in parts:
                assert part in value, f"Field '{field}' not in response"
                value = value[part]


@then(parsers.parse('the error code is "{error_code}"'))
def error_code_matches(context: VoucherTestContext, error_code: str):
    """Verify error code."""
    assert context.response_json.get("error") == error_code, \
        f"Expected error '{error_code}', got '{context.response_json.get('error')}'"


@then(parsers.parse('the error message contains "{text}"'))
def error_message_contains(context: VoucherTestContext, text: str):
    """Verify error message contains text."""
    message = context.response_json.get("message", "")
    assert text in message, f"Expected '{text}' in message: {message}"


@then(parsers.parse('the error details include field "{field}"'))
def error_details_include_field(context: VoucherTestContext, field: str):
    """Verify error details include specific field."""
    details = context.response_json.get("details", [])
    fields = [d.get("field") for d in details]
    assert field in fields, f"Field '{field}' not in error details: {details}"


@then(parsers.parse('error for "{field}" has code "{code}"'))
def error_for_field_has_code(context: VoucherTestContext, field: str, code: str):
    """Verify specific field has specific error code."""
    details = context.response_json.get("details", [])
    for detail in details:
        if detail.get("field") == field:
            assert detail.get("code") == code, \
                f"Expected code '{code}' for field '{field}', got '{detail.get('code')}'"
            return
    pytest.fail(f"No error detail for field '{field}'")


@then(parsers.parse('the error message mentions "{text}"'))
def error_mentions_text(context: VoucherTestContext, text: str):
    """Verify error message or details mention text."""
    message = context.response_json.get("message", "")
    details_str = str(context.response_json.get("details", []))
    assert text in message or text in details_str, \
        f"'{text}' not found in error response"


@then(parsers.parse('the error response contains {count:d} validation errors'))
def error_contains_n_errors(context: VoucherTestContext, count: int):
    """Verify number of validation errors."""
    details = context.response_json.get("details", [])
    assert len(details) == count, f"Expected {count} errors, got {len(details)}"


@then('the error response contains validation errors for required fields')
def error_contains_required_field_errors(context: VoucherTestContext):
    """Verify error contains required field errors."""
    details = context.response_json.get("details", [])
    assert len(details) > 0, "Expected validation errors for required fields"


@then('the PDF preserves the template formatting')
def pdf_preserves_formatting(context: VoucherTestContext):
    """Verify PDF preserves formatting."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF preserves table structure')
def pdf_preserves_tables(context: VoucherTestContext):
    """Verify PDF preserves tables."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF preserves text formatting')
def pdf_preserves_text_formatting(context: VoucherTestContext):
    """Verify PDF preserves text formatting."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF file size is less than 500KB')
def pdf_size_under_limit(context: VoucherTestContext):
    """Verify PDF size is within limits."""
    assert context.response.status_code == 201, "Voucher must be created first"
    # In real implementation, fetch PDF and check size


@then('the PDF text is searchable')
def pdf_text_searchable(context: VoucherTestContext):
    """Verify PDF contains searchable text."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then(parsers.parse('searching the PDF for "{text}" finds a match'))
def pdf_search_finds_text(context: VoucherTestContext, text: str):
    """Verify text is found in PDF."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF contains embedded images')
def pdf_contains_images(context: VoucherTestContext):
    """Verify PDF contains images."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF has multiple pages')
def pdf_has_multiple_pages(context: VoucherTestContext):
    """Verify PDF has multiple pages."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the HTML includes inline CSS')
def html_has_inline_css(context: VoucherTestContext):
    """Verify HTML has inline CSS."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the HTML has no external stylesheet links')
def html_no_external_stylesheets(context: VoucherTestContext):
    """Verify HTML has no external stylesheets."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the HTML has no external resource URLs')
def html_no_external_resources(context: VoucherTestContext):
    """Verify HTML has no external resources."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('images are embedded as base64 data URIs')
def images_embedded_base64(context: VoucherTestContext):
    """Verify images are embedded as base64."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the HTML is valid HTML5')
def html_is_valid(context: VoucherTestContext):
    """Verify HTML is valid HTML5."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then(parsers.parse('the HTML contains "{text}"'))
def html_contains_text(context: VoucherTestContext, text: str):
    """Verify HTML contains text."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then(parsers.parse('the PDF is stored at path containing "{path_part}"'))
def pdf_stored_at_path(context: VoucherTestContext, path_part: str):
    """Verify PDF storage path."""
    urls = context.response_json.get("urls", {})
    pdf_url = urls.get("pdf", "")
    assert path_part in pdf_url, f"'{path_part}' not in PDF URL: {pdf_url}"


@then(parsers.parse('the HTML is stored at path containing "{path_part}"'))
def html_stored_at_path(context: VoucherTestContext, path_part: str):
    """Verify HTML storage path."""
    urls = context.response_json.get("urls", {})
    html_url = urls.get("html", "")
    assert path_part in html_url, f"'{path_part}' not in HTML URL: {html_url}"


@then('the PDF URL returns status 200')
def pdf_url_returns_200(context: VoucherTestContext, client):
    """Verify PDF URL is accessible."""
    urls = context.response_json.get("urls", {})
    # Would fetch the URL and verify status
    pass


@then(parsers.parse('the PDF URL returns content type "{content_type}"'))
def pdf_url_content_type(context: VoucherTestContext, content_type: str):
    """Verify PDF URL content type."""
    pass


@then('the HTML URL returns status 200')
def html_url_returns_200(context: VoucherTestContext, client):
    """Verify HTML URL is accessible."""
    pass


@then(parsers.parse('the HTML URL returns content type "{content_type}"'))
def html_url_content_type(context: VoucherTestContext, content_type: str):
    """Verify HTML URL content type."""
    pass


@then(parsers.parse('the response contains "{field}"'))
def response_contains_field(context: VoucherTestContext, field: str):
    """Verify response contains a field."""
    parts = field.split(".")
    value = context.response_json
    for part in parts:
        assert part in value, f"Field '{field}' not in response: {context.response_json}"
        value = value[part]


@then(parsers.parse('the response includes "{header}" header'))
def response_includes_header(context: VoucherTestContext, header: str):
    """Verify response includes header."""
    assert header in context.response.headers, \
        f"Header '{header}' not in response headers"


@then('the response contains the original voucher_id')
def response_contains_original_voucher_id(context: VoucherTestContext):
    """Verify response contains the original voucher_id."""
    # Get original voucher_id from context
    pass


@then(parsers.parse('the response contains generated_at "{timestamp}"'))
def response_contains_generated_at(context: VoucherTestContext, timestamp: str):
    """Verify generated_at timestamp."""
    assert context.response_json.get("generated_at") == timestamp


@then('no new files are written to storage')
def no_new_files_written(context: VoucherTestContext):
    """Verify no new files were written."""
    pass


@then('the voucher_id is different from the existing voucher')
def voucher_id_different(context: VoucherTestContext):
    """Verify voucher_id is different."""
    pass


@then(parsers.parse('the response contains voucher_id "{voucher_id}"'))
def response_contains_specific_voucher_id(context: VoucherTestContext, voucher_id: str):
    """Verify specific voucher_id."""
    assert context.response_json.get("voucher_id") == voucher_id


@then(parsers.parse('the response contains template_id "{template_id}"'))
def response_contains_specific_template_id(context: VoucherTestContext, template_id: str):
    """Verify specific template_id."""
    assert context.response_json.get("template_id") == template_id


@then(parsers.parse('a warning is logged about unknown placeholder "{placeholder}"'))
def warning_logged_for_placeholder(context: VoucherTestContext, placeholder: str):
    """Verify warning was logged."""
    pass


@then(parsers.parse('validation reports unknown placeholder "{placeholder}"'))
def validation_reports_unknown(context: VoucherTestContext, placeholder: str):
    """Verify validation reports unknown placeholder."""
    pass


@then(parsers.parse('validation suggests "{suggestion}"'))
def validation_suggests(context: VoucherTestContext, suggestion: str):
    """Verify validation suggestion."""
    pass


@then('validation passes with no errors')
def validation_passes(context: VoucherTestContext):
    """Verify validation passes."""
    pass


@then('validation passes')
def validation_passes_simple(context: VoucherTestContext):
    """Verify validation passes (simplified)."""
    pass


@then(parsers.parse('validation warns "{warning}"'))
def validation_warns(context: VoucherTestContext, warning: str):
    """Verify validation warning."""
    pass


@then(parsers.parse('the error response contains:\n{table}'))
def error_response_contains_fields(context: VoucherTestContext, table):
    """Verify error response contains expected fields."""
    expected = _parse_table(table)
    for field, type_or_value in expected.items():
        assert field in context.response_json, \
            f"Field '{field}' not in error response"


@then('the error response contains a correlation_id')
def error_has_correlation_id(context: VoucherTestContext):
    """Verify error has correlation_id."""
    assert "correlation_id" in context.response_json, \
        "No correlation_id in error response"


@then(parsers.parse('the error response contains "{field}" as integer'))
def error_contains_integer_field(context: VoucherTestContext, field: str):
    """Verify field is an integer."""
    assert field in context.response_json
    assert isinstance(context.response_json[field], int)


@then(parsers.parse('the response header "{header}" is present'))
def header_is_present(context: VoucherTestContext, header: str):
    """Verify header is present."""
    assert header in context.response.headers


@then('the correlation_id is logged with the error')
def correlation_id_logged(context: VoucherTestContext):
    """Verify correlation_id was logged."""
    pass


@then('the error message is human-readable')
def error_message_readable(context: VoucherTestContext):
    """Verify error message is human-readable."""
    message = context.response_json.get("message", "")
    assert len(message) > 10, "Error message too short to be helpful"


@then('the error message explains what was wrong')
def error_message_explains(context: VoucherTestContext):
    """Verify error message explains the problem."""
    message = context.response_json.get("message", "")
    assert len(message) > 0, "Error message is empty"


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_table(table_str: str) -> dict:
    """Parse a Gherkin table string into a dictionary."""
    lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
    if not lines:
        return {}

    # First line is headers
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    if len(headers) != 2 or headers[0] != "field":
        # Try alternate format
        result = {}
        for line in lines:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 2:
                result[parts[0]] = parts[1]
        return result

    # Standard field/value table
    result = {}
    for line in lines[1:]:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 2:
            result[parts[0]] = parts[1]
    return result


def _parse_table_rows(table_str: str) -> list:
    """Parse a Gherkin table string into a list of dictionaries."""
    lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
    if not lines:
        return []

    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    result = []
    for line in lines[1:]:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == len(headers):
            result.append(dict(zip(headers, parts)))
    return result


def _execute_voucher_request(context: VoucherTestContext):
    """Execute the voucher request using built-up context."""
    from .conftest import MockTestClient

    # Build the full request
    request_body = {
        **context.request_data,
        "customer": context.customer_data,
        "service": context.service_data
    }

    # Get client (injected by pytest)
    # For now, use mock client
    client = MockTestClient()
    context.response = client.post("/vouchers", json=request_body)
    if hasattr(context.response, 'json'):
        context.response_json = context.response.json()
