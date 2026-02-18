"""GenerateVoucher use case - orchestrates voucher generation workflow."""

from dataclasses import dataclass
from datetime import UTC, datetime

from voucher_merger.domain.value_objects import BookingRef, CustomerData, ServiceData
from voucher_merger.ports.document_renderer import DocumentRenderer, MergedContent
from voucher_merger.ports.template_repository import TemplateRepository
from voucher_merger.ports.voucher_storage import VoucherStorage


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
    """

    pdf_url: str


@dataclass(frozen=True)
class VoucherResponse:
    """Response object containing the generated voucher details.

    Attributes:
        voucher_id: Unique identifier for the generated voucher.
        urls: URLs where the voucher can be accessed.
        generated_at: Timestamp when the voucher was generated.
    """

    voucher_id: str
    urls: VoucherUrls
    generated_at: datetime


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

    def execute(self, request: GenerateVoucherRequest) -> VoucherResponse:
        """Execute the voucher generation workflow.

        Args:
            request: The voucher generation request.

        Returns:
            VoucherResponse with generated voucher details.

        Raises:
            TemplateNotFoundError: If the requested template is not found.
        """
        # 1. Load template
        template = self._template_repository.find_by_id(request.template_id)
        if template is None:
            raise TemplateNotFoundError(request.template_id)

        # 2. Merge customer data into template
        merged_html = self._merge_template(template.content, request)
        merged_content = MergedContent(html=merged_html)

        # 3. Render to PDF
        rendered_document = self._document_renderer.render_pdf(merged_content)

        # 4. Store voucher
        storage_url = self._voucher_storage.store(rendered_document)

        # 5. Build and return response
        voucher_id = self._generate_voucher_id(request.booking)
        return VoucherResponse(
            voucher_id=voucher_id,
            urls=VoucherUrls(pdf_url=storage_url.url),
            generated_at=datetime.now(UTC),
        )

    def _merge_template(
        self, template_content: str, request: GenerateVoucherRequest
    ) -> str:
        """Merge request data into template placeholders.

        Replaces all {{customer.*}} placeholders with customer data.
        Missing optional fields are rendered as empty strings.

        Args:
            template_content: Raw template content with placeholders.
            request: Request containing data for merge.

        Returns:
            Merged content with placeholders replaced.
        """
        customer = request.customer

        # Build customer placeholder mappings
        customer_placeholders = {
            "{{customer.first_name}}": customer.first_name,
            "{{customer.last_name}}": customer.last_name,
            "{{customer.title}}": customer.title or "",
            "{{customer.email}}": customer.email or "",
            "{{customer.phone}}": customer.phone or "",
        }

        merged = template_content
        for placeholder, value in customer_placeholders.items():
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
