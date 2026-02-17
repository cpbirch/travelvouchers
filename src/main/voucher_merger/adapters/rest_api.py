"""REST API adapter for voucher generation.

This module provides the FastAPI router for the voucher generation endpoint.
It translates HTTP requests to use case calls and formats responses.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from voucher_merger.application.generate_voucher import (
    GenerateVoucher,
    GenerateVoucherRequest,
    VoucherResponse,
)
from voucher_merger.domain.value_objects import BookingRef, CustomerData, ServiceData

# =============================================================================
# Request/Response Models
# =============================================================================


class CustomerRequest(BaseModel):
    """Customer data in the API request."""

    first_name: str = Field(..., description="Customer's first name")
    last_name: str = Field(..., description="Customer's last name")
    title: Optional[str] = Field(None, description="Optional title (Mr., Dr., etc.)")


class ServiceRequest(BaseModel):
    """Service data in the API request."""

    name: str = Field(..., description="Name of the service")
    provider: str = Field(..., description="Service provider name")


class VoucherRequest(BaseModel):
    """Request body for POST /vouchers."""

    template_id: str = Field(..., description="Template identifier to use")
    booking_id: str = Field(..., description="Booking identifier")
    service_date: str = Field(..., description="Service date in YYYY-MM-DD format")
    customer: CustomerRequest = Field(..., description="Customer information")
    service: ServiceRequest = Field(..., description="Service information")


class UrlsResponse(BaseModel):
    """URLs in the API response."""

    pdf: str = Field(..., description="URL to the generated PDF")


class VoucherApiResponse(BaseModel):
    """Response body for POST /vouchers."""

    voucher_id: str = Field(..., description="Generated voucher identifier")
    booking_id: str = Field(..., description="Original booking identifier")
    service_date: str = Field(..., description="Service date")
    template_id: str = Field(..., description="Template used for generation")
    generated_at: str = Field(..., description="ISO timestamp of generation")
    urls: UrlsResponse = Field(..., description="URLs to access the voucher")


# =============================================================================
# Router
# =============================================================================


def create_voucher_router(generate_voucher: GenerateVoucher) -> APIRouter:
    """Create the voucher API router with injected use case.

    Args:
        generate_voucher: The use case for generating vouchers.

    Returns:
        FastAPI router with voucher endpoints.
    """
    router = APIRouter(tags=["vouchers"])

    @router.post(
        "/vouchers",
        response_model=VoucherApiResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Generate a voucher",
        description="Generate a PDF voucher from a template.",
    )
    def create_voucher(request: VoucherRequest) -> VoucherApiResponse:
        """Generate a voucher from the provided data.

        Args:
            request: The voucher generation request.

        Returns:
            The generated voucher details including URLs.
        """
        # Parse service_date string to date object
        service_date = date.fromisoformat(request.service_date)

        # Build domain objects
        booking = BookingRef(
            booking_id=request.booking_id,
            service_date=service_date,
        )
        customer = CustomerData(
            first_name=request.customer.first_name,
            last_name=request.customer.last_name,
            title=request.customer.title,
        )
        service = ServiceData(
            name=request.service.name,
            provider=request.service.provider,
        )

        # Build use case request
        use_case_request = GenerateVoucherRequest(
            template_id=request.template_id,
            booking=booking,
            customer=customer,
            service=service,
        )

        # Execute use case
        result: VoucherResponse = generate_voucher.execute(use_case_request)

        # Format response
        return VoucherApiResponse(
            voucher_id=result.voucher_id,
            booking_id=request.booking_id,
            service_date=request.service_date,
            template_id=request.template_id,
            generated_at=result.generated_at.isoformat(),
            urls=UrlsResponse(pdf=result.urls.pdf_url),
        )

    return router
