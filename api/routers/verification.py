"""
Verification router for the FastAPI backend.

Provides endpoints for verifying result consistency across calculation methods.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.responses import VerificationResult
from services.database import DatabaseService, get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["verification"])


@router.get("/results/verify", response_model=VerificationResult)
async def verify_results(
    tolerance: Optional[float] = Query(
        default=1e-9,
        description="Floating-point comparison tolerance for result verification",
        ge=0,
    ),
    db: DatabaseService = Depends(get_database_service),
) -> VerificationResult:
    """
    Verify that all calculation methods produce identical results.

    Compares results across all three methods (.NET, Python, SQL) for
    each data record and formula, checking for discrepancies within
    the specified floating-point tolerance.

    **Validates: Requirement 7.1** - Verifies results are identical across
    all calculation methods.

    Args:
        tolerance: Maximum allowed difference between results (default: 1e-9).

    Returns:
        VerificationResult containing:
        - is_valid: True if all methods agree within tolerance
        - tolerance: The tolerance used for comparison
        - total_records_checked: Total number of result comparisons performed
        - total_discrepancies: Number of discrepancies found
        - discrepancies: List of discrepancies (limited to first 100)
        - methods_compared: List of methods that were compared
        - verification_timestamp: When verification was performed
    """
    try:
        result = await db.verify_results(tolerance=tolerance)
        return VerificationResult(**result)
    except Exception as e:
        logger.error(f"Failed to verify results: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify results")
