"""
Formulas router for the FastAPI backend.

Provides endpoints for fetching formula definitions from the database.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from schemas.responses import Formula
from services.database import DatabaseService, get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["formulas"])


@router.get("/formulas", response_model=List[Formula])
async def get_formulas(
    db: DatabaseService = Depends(get_database_service),
) -> List[Formula]:
    """
    Get all formulas from the t_targil table.

    Returns a list of formula definitions including:
    - targil_id: Unique formula identifier
    - targil: Main formula expression
    - tnai: Condition expression (if any)
    - targil_false: Formula when condition is false
    - description: Formula description
    - complexity_level: Complexity level (simple, complex, conditional)
    """
    try:
        formulas = await db.get_formulas()
        return [Formula(**formula) for formula in formulas]
    except Exception as e:
        logger.error(f"Failed to fetch formulas: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch formulas")
