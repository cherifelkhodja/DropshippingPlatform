"""Product endpoints.

Provides endpoints for direct product access (not nested under pages).
"""

from fastapi import APIRouter

from src.app.api.schemas.products import ProductResponse, product_to_response
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import ProductRepo
from src.app.core.domain.errors import EntityNotFoundError


router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Get detailed information about a specific product.",
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_product(
    product_id: str,
    product_repo: ProductRepo,
) -> ProductResponse:
    """Get details of a specific product by ID.

    Returns the full product details including pricing, availability,
    tags, and metadata.
    """
    product = await product_repo.get_by_id(product_id)

    if product is None:
        raise EntityNotFoundError("Product", product_id)

    return product_to_response(product)
