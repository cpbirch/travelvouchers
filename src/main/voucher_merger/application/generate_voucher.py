"""GenerateVoucher use case - orchestrates voucher generation workflow."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from voucher_merger.domain.placeholder_validator import PlaceholderValidator
from voucher_merger.domain.template import TemplatePlaceholderExtractor
from voucher_merger.domain.value_objects import BookingRef, CustomerData, ServiceData
from voucher_merger.ports.document_renderer import DocumentRenderer, MergedContent
from voucher_merger.ports.template_repository import TemplateRepository
from voucher_merger.ports.voucher_storage import VoucherStorage

logger = logging.getLogger(__name__)


class TemplateNotFoundError(Exception):
    """Raised when the requested template cannot be found."""

    def __init__(self, template_id: str) -> None:
        self.template_id = template_id
        super().__init__(f"Template not found: {template_id}")


@dataclass(frozen=True)
class GenerateVoucherRequest:
    """Request object for voucher generation.

    Attributes:
        template_id: Identifier of the template to use.
        booking: Booking reference information.
        customer: Customer data for personalization.
        service: Service data for the voucher.
    """

    template_id: str
    booking: BookingRef
    customer: CustomerData
    service: ServiceData


@dataclass(frozen=True)
class VoucherUrls:
    """URLs where the generated voucher can be accessed.

    Attributes:
        pdf_url: URL to the PDF version of the voucher.
        html_url: URL to the HTML version of the voucher.
    """

    pdf_url: str
    html_url: str | None = None


@dataclass(frozen=True)
class VoucherResponse:
    """Response object containing the generated voucher details.

    Attributes:
        voucher_id: Unique identifier for the generated voucher.
        urls: URLs where the voucher can be accessed.
        generated_at: Timestamp when the voucher was generated.
        is_existing: Whether this is an existing voucher (False for new).
    """

    voucher_id: str
    urls: VoucherUrls
    generated_at: datetime
    is_existing: bool = False


@dataclass(frozen=True)
class ExistingVoucherResponse:
    """Response object for an existing voucher (idempotency).

    Attributes:
        voucher_id: Unique identifier for the existing voucher.
        urls: URLs where the voucher can be accessed.
        generated_at: Original timestamp when the voucher was generated.
        is_existing: Always True for existing vouchers.
    """

    voucher_id: str
    urls: VoucherUrls
    generated_at: str  # ISO string from stored metadata
    is_existing: bool = True


class GenerateVoucher:
    """Use case for generating vouchers.

    Orchestrates the voucher generation workflow:
    1. Load template via TemplateRepository port
    2. Merge customer/service data into template placeholders
    3. Render to PDF via DocumentRenderer port
    4. Store via VoucherStorage port
    5. Return VoucherResponse with voucher details
    """

    def __init__(
        self,
        template_repository: TemplateRepository,
        document_renderer: DocumentRenderer,
        voucher_storage: VoucherStorage,
    ) -> None:
        """Initialize use case with required ports.

        Args:
            template_repository: Port for loading templates.
            document_renderer: Port for rendering documents to PDF.
            voucher_storage: Port for storing generated vouchers.
        """
        self._template_repository = template_repository
        self._document_renderer = document_renderer
        self._voucher_storage = voucher_storage

    def execute(
        self, request: GenerateVoucherRequest
    ) -> VoucherResponse | ExistingVoucherResponse:
        """Execute the voucher generation workflow.

        Args:
            request: The voucher generation request.

        Returns:
            VoucherResponse with generated voucher details, or
            ExistingVoucherResponse if a voucher already exists (idempotency).

        Raises:
            TemplateNotFoundError: If the requested template is not found.
        """
        # 0. Configure storage with booking context (if supported)
        # This must happen BEFORE idempotency check
        if hasattr(self._voucher_storage, "configure"):
            service_date_str = request.booking.service_date.strftime("%Y-%m-%d")
            self._voucher_storage.configure(
                booking_id=request.booking.booking_id,
                service_date=service_date_str,
            )

        # 1. Check for existing voucher (idempotency)
        existing = self._voucher_storage.find_existing()
        if existing is not None:
            # Return existing voucher metadata
            # Handle both dict (from test fixtures) and VoucherMetadata (from real storage)
            if isinstance(existing, dict):
                return ExistingVoucherResponse(
                    voucher_id=existing.get("voucher_id", ""),
                    urls=VoucherUrls(
                        pdf_url=existing.get("pdf_url", ""),
                        html_url=existing.get("html_url"),
                    ),
                    generated_at=existing.get("generated_at", ""),
                    is_existing=True,
                )
            else:
                # VoucherMetadata dataclass
                return ExistingVoucherResponse(
                    voucher_id=existing.voucher_id,
                    urls=VoucherUrls(
                        pdf_url=existing.pdf_url,
                        html_url=existing.html_url,
                    ),
                    generated_at=existing.generated_at,
                    is_existing=True,
                )

        # 2. Load template
        template = self._template_repository.find_by_id(request.template_id)
        if template is None:
            raise TemplateNotFoundError(request.template_id)

        # 2a. Validate template placeholders (non-blocking)
        self._validate_placeholders(template.content, request.template_id)

        # 3. Merge customer data into template
        merged_html = self._merge_template(template.content, request)
        merged_content = MergedContent(html=merged_html)

        # 4. Render to PDF
        rendered_document = self._document_renderer.render_pdf(merged_content)

        # 5. Render to email-compatible HTML
        rendered_html = self._document_renderer.render_html(merged_content)

        # 6. Store vouchers (PDF and HTML)
        pdf_storage_url = self._voucher_storage.store(rendered_document)
        html_storage_url = self._voucher_storage.store_html(rendered_html)

        # 7. Build and return response
        voucher_id = self._generate_voucher_id(request.booking)
        return VoucherResponse(
            voucher_id=voucher_id,
            urls=VoucherUrls(
                pdf_url=pdf_storage_url.url,
                html_url=html_storage_url.url,
            ),
            generated_at=datetime.now(UTC),
        )

    def _merge_template(
        self, template_content: str, request: GenerateVoucherRequest
    ) -> str:
        """Merge request data into template placeholders.

        Replaces all {{customer.*}} and {{service.*}} placeholders with data.
        Missing optional fields are rendered as empty strings.

        Args:
            template_content: Raw template content with placeholders.
            request: Request containing data for merge.

        Returns:
            Merged content with placeholders replaced.
        """
        customer = request.customer
        service = request.service

        # Build customer placeholder mappings
        customer_placeholders = {
            "{{customer.first_name}}": customer.first_name,
            "{{customer.last_name}}": customer.last_name,
            "{{customer.title}}": customer.title or "",
            "{{customer.email}}": customer.email or "",
            "{{customer.phone}}": customer.phone or "",
        }

        # Build service placeholder mappings
        service_placeholders = {
            "{{service.name}}": service.name,
            "{{service.provider}}": service.provider,
            "{{service.pickup_time}}": service.pickup_time or "",
            "{{service.pickup_location}}": service.pickup_location or "",
            "{{service.dropoff_location}}": service.dropoff_location or "",
            "{{service.passengers}}": service.passengers or "",
            "{{service.confirmation_code}}": service.confirmation_code or "",
            "{{service.meeting_point}}": service.meeting_point or "",
            "{{service.tour_time}}": service.tour_time or "",
            "{{service.duration}}": service.duration or "",
            "{{service.notes}}": service.notes or "",
        }

        merged = template_content
        for placeholder, value in customer_placeholders.items():
            merged = merged.replace(placeholder, value)

        for placeholder, value in service_placeholders.items():
            merged = merged.replace(placeholder, value)

        return merged

    def _generate_voucher_id(self, booking: BookingRef) -> str:
        """Generate a unique voucher identifier.

        Format: V-{booking_id}-{date}

        Args:
            booking: Booking reference for ID generation.

        Returns:
            Generated voucher ID.
        """
        date_str = booking.service_date.strftime("%Y%m%d")
        return f"V-{booking.booking_id}-{date_str}"

    def _validate_placeholders(self, template_content: str, template_id: str) -> None:
        """Validate template placeholders and log warnings.

        This validation is non-blocking - it logs warnings but allows generation
        to proceed even with unknown or optional placeholders.

        Args:
            template_content: Raw template content to validate.
            template_id: Template identifier for logging context.
        """
        extractor = TemplatePlaceholderExtractor()
        extracted = extractor.extract_placeholders(template_content)

        validator = PlaceholderValidator()
        result = validator.validate(extracted)

        # Log warnings for unknown placeholders
        for placeholder in result.unknown_placeholders:
            suggestion = result.suggestions.get(placeholder)
            if suggestion:
                logger.warning(
                    "Template '%s' contains unknown placeholder '%s'. "
                    "Did you mean: %s?",
                    template_id,
                    placeholder,
                    suggestion,
                )
            else:
                logger.warning(
                    "Template '%s' contains unknown placeholder '%s'.",
                    template_id,
                    placeholder,
                )

        # Log warnings for optional field usage
        for warning in result.warnings:
            logger.warning("Template '%s': %s", template_id, warning)
