from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List
import uuid

from app.db.database import get_db
from app.models import schemas
from app.models.models import Expert
from app.services.ai_service import get_llm_service

router = APIRouter(prefix="/experts", tags=["experts"])

@router.get("", response_model=schemas.ExpertListResponse)
async def list_experts(
    country: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    query: Optional[str] = Query(None, description="Semantic search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List experts with filters and semantic search.
    
    Example: /api/experts?country=UAE&specialty=Legal&page=1
    """
    q = db.query(Expert).filter(Expert.is_active == True)
    
    # Apply filters
    if country:
        q = q.filter(Expert.country.ilike(f"%{country}%"))
    
    if specialty:
        q = q.filter(Expert.specialties.any(lambda x: x.ilike(f"%{specialty}%")))
    
    if language:
        q = q.filter(Expert.languages.any(lambda x: x.ilike(f"%{language}%")))
    
    if min_rating:
        q = q.filter(Expert.rating >= min_rating)
    
    # Semantic search with query text
    if query:
        llm = get_llm_service()
        embedding = await llm.get_embedding(query)
        
        if embedding and False:  # Disabled until pgvector is fully set up
            # Would use pgvector <=> operator here
            pass
        else:
            # Fallback to text search
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    Expert.name.ilike(search_term),
                    Expert.company.ilike(search_term),
                    Expert.bio.ilike(search_term),
                    Expert.country.ilike(search_term)
                )
            )
    
    # Get total count
    total = q.count()
    
    # Pagination
    experts = q.order_by(Expert.rating.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return schemas.ExpertListResponse(
        total=total,
        page=page,
        page_size=page_size,
        experts=[schemas.ExpertResponse.from_orm(e) for e in experts]
    )

@router.get("/{expert_id}", response_model=schemas.ExpertResponse)
async def get_expert(expert_id: uuid.UUID, db: Session = Depends(get_db)):
    expert = db.query(Expert).filter(Expert.id == expert_id, Expert.is_active == True).first()
    if not expert:
        raise HTTPException(status_code=404, detail="Expert not found")
    return expert

@router.get("/search/semantic")
async def search_experts_semantic(
    query: str,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Semantic search for experts using vector similarity.
    """
    llm = get_llm_service()
    embedding = await llm.get_embedding(query)
    
    if not embedding:
        return {"error": "AI service unavailable", "results": []}
    
    # Find experts with embeddings
    experts = db.query(Expert).filter(
        Expert.is_active == True,
        Expert.profile_embedding.isnot(None)
    ).all()
    
    # Calculate similarity
    import numpy as np
    query_vec = np.array(embedding)
    
    scored = []
    for expert in experts:
        if expert.profile_embedding:
            expert_vec = np.array(expert.profile_embedding)
            sim = np.dot(query_vec, expert_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(expert_vec))
            scored.append((expert, float(sim)))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]
    
    return {
        "query": query,
        "results": [
            {
                "expert": schemas.ExpertResponse.from_orm(e),
                "similarity_score": round(s, 3)
            }
            for e, s in top
        ]
    }
