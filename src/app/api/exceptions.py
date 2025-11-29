"""API Exception Handlers.

Translates domain errors to HTTP responses.
"""

import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.app.core.domain.errors import (
    DomainError,
    EntityNotFoundError,
    InvalidCategoryError,
    InvalidCountryError,
    InvalidCurrencyError,
    InvalidLanguageError,
    InvalidPageStateError,
    InvalidPaymentMethodError,
    InvalidProductCountError,
    InvalidScanIdError,
    InvalidUrlError,
    MetaAdsApiError,
    MetaAdsAuthenticationError,
    MetaAdsRateLimitError,
    RepositoryError,
    ScrapingBlockedError,
    ScrapingError,
    ScrapingTimeoutError,
    SitemapNotFoundError,
    SitemapParsingError,
    TaskDispatchError,
)


def create_error_response(
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response."""
    response: dict[str, Any] = {
        "error": error,
        "message": message,
    }
    if details:
        response["details"] = details
    return response


async def domain_validation_error_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    """Handle domain validation errors (400 Bad Request)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error=exc.__class__.__name__,
            message=str(exc),
            details={"value": exc.value} if exc.value is not None else None,
        ),
    )


async def entity_not_found_handler(
    request: Request,
    exc: EntityNotFoundError,
) -> JSONResponse:
    """Handle entity not found errors (404 Not Found)."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            error="EntityNotFound",
            message=str(exc),
            details={"entity_id": exc.value},
        ),
    )


async def meta_ads_rate_limit_handler(
    request: Request,
    exc: MetaAdsRateLimitError,
) -> JSONResponse:
    """Handle Meta Ads rate limit errors (429 Too Many Requests)."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=create_error_response(
            error="RateLimitExceeded",
            message=str(exc),
        ),
    )


async def meta_ads_auth_handler(
    request: Request,
    exc: MetaAdsAuthenticationError,
) -> JSONResponse:
    """Handle Meta Ads authentication errors (401 Unauthorized)."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=create_error_response(
            error="AuthenticationFailed",
            message="Meta Ads API authentication failed",
        ),
    )


async def meta_ads_error_handler(
    request: Request,
    exc: MetaAdsApiError,
) -> JSONResponse:
    """Handle generic Meta Ads API errors (502 Bad Gateway)."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=create_error_response(
            error="ExternalServiceError",
            message=str(exc),
        ),
    )


async def scraping_blocked_handler(
    request: Request,
    exc: ScrapingBlockedError,
) -> JSONResponse:
    """Handle scraping blocked errors (403 Forbidden)."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=create_error_response(
            error="ScrapingBlocked",
            message=str(exc),
            details={"url": exc.value},
        ),
    )


async def scraping_timeout_handler(
    request: Request,
    exc: ScrapingTimeoutError,
) -> JSONResponse:
    """Handle scraping timeout errors (504 Gateway Timeout)."""
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=create_error_response(
            error="ScrapingTimeout",
            message=str(exc),
            details={"url": exc.value},
        ),
    )


async def scraping_error_handler(
    request: Request,
    exc: ScrapingError,
) -> JSONResponse:
    """Handle generic scraping errors (502 Bad Gateway)."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=create_error_response(
            error="ScrapingError",
            message=str(exc),
            details={"url": exc.value},
        ),
    )


async def sitemap_not_found_handler(
    request: Request,
    exc: SitemapNotFoundError,
) -> JSONResponse:
    """Handle sitemap not found errors (404 Not Found)."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            error="SitemapNotFound",
            message=str(exc),
            details={"website": exc.value},
        ),
    )


async def sitemap_parsing_handler(
    request: Request,
    exc: SitemapParsingError,
) -> JSONResponse:
    """Handle sitemap parsing errors (422 Unprocessable Entity)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            error="SitemapParsingError",
            message=str(exc),
            details={"sitemap_url": exc.value},
        ),
    )


async def repository_error_handler(
    request: Request,
    exc: RepositoryError,
) -> JSONResponse:
    """Handle repository/database errors (500 Internal Server Error)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error="DatabaseError",
            message="A database error occurred",
        ),
    )


async def task_dispatch_error_handler(
    request: Request,
    exc: TaskDispatchError,
) -> JSONResponse:
    """Handle task dispatch errors (503 Service Unavailable)."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=create_error_response(
            error="TaskDispatchError",
            message=str(exc),
        ),
    )


async def generic_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected errors (500 Internal Server Error)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error="InternalError",
            message="An unexpected error occurred",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application.

    Exception mappings:
    - EntityNotFoundError → 404 Not Found
    - MetaAdsRateLimitError → 429 Too Many Requests
    - MetaAdsAuthenticationError → 401 Unauthorized
    - MetaAdsApiError → 502 Bad Gateway
    - ScrapingBlockedError → 403 Forbidden
    - ScrapingTimeoutError → 504 Gateway Timeout
    - ScrapingError → 502 Bad Gateway
    - SitemapNotFoundError → 404 Not Found
    - SitemapParsingError → 422 Unprocessable Entity
    - RepositoryError → 500 Internal Server Error
    - TaskDispatchError → 503 Service Unavailable
    - DomainError (validation) → 400 Bad Request
    """
    # Specific errors first (more specific to less specific)
    # 404 Not Found
    app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)
    app.add_exception_handler(SitemapNotFoundError, sitemap_not_found_handler)

    # 401/429 Meta Ads errors
    app.add_exception_handler(MetaAdsRateLimitError, meta_ads_rate_limit_handler)
    app.add_exception_handler(MetaAdsAuthenticationError, meta_ads_auth_handler)
    app.add_exception_handler(MetaAdsApiError, meta_ads_error_handler)

    # Scraping errors (403, 504, 502)
    app.add_exception_handler(ScrapingBlockedError, scraping_blocked_handler)
    app.add_exception_handler(ScrapingTimeoutError, scraping_timeout_handler)
    app.add_exception_handler(ScrapingError, scraping_error_handler)

    # Sitemap parsing → 422
    app.add_exception_handler(SitemapParsingError, sitemap_parsing_handler)

    # Infrastructure errors
    app.add_exception_handler(RepositoryError, repository_error_handler)
    app.add_exception_handler(TaskDispatchError, task_dispatch_error_handler)

    # Domain validation errors (400 Bad Request)
    validation_errors = [
        InvalidUrlError,
        InvalidCountryError,
        InvalidLanguageError,
        InvalidCurrencyError,
        InvalidProductCountError,
        InvalidPageStateError,
        InvalidCategoryError,
        InvalidScanIdError,
        InvalidPaymentMethodError,
    ]
    for error_class in validation_errors:
        app.add_exception_handler(error_class, domain_validation_error_handler)


def create_request_logging_middleware(
    logger: Any,
) -> Callable[[Request, Callable[..., Any]], Any]:
    """Create a middleware for logging requests."""

    async def log_requests(
        request: Request,
        call_next: Callable[..., Any],
    ) -> Any:
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "HTTP request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

    return log_requests
