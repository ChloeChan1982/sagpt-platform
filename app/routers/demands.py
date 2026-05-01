from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.database import get_db
from app.models import schemas
from app.models.models import Demand, Expert, ChatSession
from app.services.ai_service import get_llm_service, get_matching_service

router = APIRouter(prefix="/demands", tags=["demands"])

@router.post("/submit", response_model=schemas.DemandSubmitResponse)
async def submit_demand(
    request: Request,
    demand_data: schemas.DemandCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submit a new demand and get instant AI match preview.
    This replaces the static Readdy form submission.
    """
    # Create demand record
    demand = Demand(
        target_country=demand_data.target_country,
        industry=demand_data.industry,
        scenario=demand_data.scenario,
        budget_range=demand_data.budget_range,
        urgency=demand_data.urgency,
        description=demand_data.description,
        email=demand_data.email,
        wechat_phone=demand_data.wechat_phone,
        company_name=demand_data.company_name,
        phone=demand_data.phone,
        attachments=demand_data.attachments or [],
        status="pending",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    db.add(demand)
    db.commit()
    db.refresh(demand)
    
    # Generate embedding in background
    llm = get_llm_service()
    embedding = await llm.get_embedding(
        f"Country: {demand.target_country}. Industry: {demand.industry}. "
        f"Scenario: {demand.scenario}. Need: {demand.description}"
    )
    if embedding:
        demand.description_embedding = embedding
        db.commit()
    
    # Get instant AI matches
    matcher = get_matching_service()
    matches = await matcher.find_matches(db, demand, top_k=5, min_score=0.2)
    
    # Update demand with match results
    demand.matched_expert_ids = [m.expert_id for m in matches[:3]]
    demand.ai_match_score = matches[0].match_score if matches else 0.0
    demand.status = "matching"
    db.commit()
    
    return schemas.DemandSubmitResponse(
        success=True,
        demand_id=demand.id,
        message="Your demand has been submitted successfully! Our AI is analyzing your needs.",
        estimated_match_time="within 24 hours",
        preview_matches=matches
    )

@router.get("/{demand_id}", response_model=schemas.DemandResponse)
async def get_demand(demand_id: uuid.UUID, db: Session = Depends(get_db)):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    return demand

@router.get("/{demand_id}/matches", response_model=List[schemas.MatchPreview])
async def get_demand_matches(
    demand_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    
    matcher = get_matching_service()
    matches = await matcher.find_matches(db, demand, top_k=8, min_score=0.2)
    return matches

@router.post("/{demand_id}/rematch")
async def rematch_demand(
    demand_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Trigger re-matching with updated algorithms"""
    demand = db.query(Demand).filter(Demand.id == demand_id).first()
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    
    # Regenerate embedding
    llm = get_llm_service()
    embedding = await llm.get_embedding(
        f"Country: {demand.target_country}. Industry: {demand.industry}. "
        f"Scenario: {demand.scenario}. Need: {demand.description}"
    )
    if embedding:
        demand.description_embedding = embedding
    
    matcher = get_matching_service()
    matches = await matcher.find_matches(db, demand, top_k=5)
    
    demand.matched_expert_ids = [m.expert_id for m in matches[:3]]
    demand.status = "matching"
    db.commit()
    
    return {"success": True, "matches_count": len(matches), "matches": matches}

@router.get("/stats/summary")
async def get_demand_stats(db: Session = Depends(get_db)):
    """Dashboard stats for admin"""
    total = db.query(func.count(Demand.id)).scalar()
    pending = db.query(func.count(Demand.id)).filter(Demand.status == "pending").scalar()
    matched = db.query(func.count(Demand.id)).filter(Demand.status == "matched").scalar()
    
    # Top countries
    top_countries = db.query(
        Demand.target_country,
        func.count(Demand.id).label("count")
    ).group_by(Demand.target_country).order_by(func.count(Demand.id).desc()).limit(5).all()
    
    return {
        "total_demands": total,
        "pending": pending,
        "matched": matched,
        "top_countries": [{"country": c[0], "count": c[1]} for c in top_countries]
    }
