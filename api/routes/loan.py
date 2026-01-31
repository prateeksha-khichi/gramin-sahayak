"""
Loan API routes
"""

from fastapi import APIRouter, HTTPException
from api.schemas.request_response import LoanRequest, LoanResponse
from services.loan_service import LoanService
from database.db_manager import db
from loguru import logger

router = APIRouter(prefix="/loan", tags=["Loan"])
loan_service = LoanService()


@router.post("/check-eligibility", response_model=LoanResponse)
async def check_loan_eligibility(request: LoanRequest):
    """
    Check loan eligibility and calculate EMI
    """
    try:
        user_data = request.dict()
        result = loan_service.predict_eligibility(user_data)
        
        # Save to database (use a default user_id for API calls)
        db_data = {
            'user_telegram_id': 'api_user',
            **user_data,
            **{k: v for k, v in result.items() if k not in ['message_hindi', 'message_english']}
        }
        db.save_loan_query(db_data)
        
        return LoanResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Loan API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemes")
async def get_government_schemes():
    """
    Get list of verified government loan schemes
    """
    schemes = [
        {
            "name": "प्रधानमंत्री मुद्रा योजना (PM MUDRA)",
            "max_amount": 1000000,
            "purpose": "Business",
            "interest_rate": "8-12%",
            "verified": True
        },
        {
            "name": "किसान क्रेडिट कार्ड (KCC)",
            "max_amount": 300000,
            "purpose": "Agriculture",
            "interest_rate": "4-7%",
            "verified": True
        },
        {
            "name": "Stand Up India",
            "max_amount": 10000000,
            "purpose": "SC/ST/Women entrepreneurs",
            "interest_rate": "Base rate + margin",
            "verified": True
        }
    ]
    
    return {"schemes": schemes, "count": len(schemes)}