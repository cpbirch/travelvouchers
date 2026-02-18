"""Test constants - extract magic strings and values.

L1 Readability: Extract magic strings/numbers to named constants.
"""

# Standard test URLs
PDF_URL_PREFIX = "file:///vouchers"
HTML_URL_PREFIX = "file:///vouchers"
DEFAULT_PDF_URL = f"{PDF_URL_PREFIX}/test/voucher.pdf"
DEFAULT_HTML_URL = f"{HTML_URL_PREFIX}/test/voucher.html"

# Standard test template IDs
SKELETON_TEMPLATE_ID = "skeleton-template"
AIRPORT_TRANSFER_TEMPLATE_ID = "airport-transfer-v2"
SIGHTSEEING_TOUR_TEMPLATE_ID = "sightseeing-tour-v1"

# Standard test booking IDs
DEFAULT_BOOKING_ID = "BK-2024-00001"
DEFAULT_SERVICE_DATE = "2024-01-01"

# Standard test customer data
DEFAULT_FIRST_NAME = "James"
DEFAULT_LAST_NAME = "Morrison"

# Standard test service data
DEFAULT_SERVICE_NAME = "Airport Transfer"
DEFAULT_SERVICE_PROVIDER = "CityLink Transfers"

# PDF structure markers
PDF_HEADER = b"%PDF-1.4"
PDF_TEST_CONTENT = b"%PDF-1.4\n%test content\n%%EOF"
PDF_MINIMAL = b"%PDF-1.4\n%%EOF"

# HTTP status codes (for clarity)
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503
