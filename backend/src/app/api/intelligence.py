from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Entity, EntityLink, NormalizedResult, User
from app.api.evidence import _build_graph_for_entity
from app.services.intelligence_card import IntelligenceCardGenerator
from app.services.synthesis import SynthesisService
from app.services.security import get_current_user
from app.schemas import IntelligenceCardResponse, SynthesisResponse

router = APIRouter(prefix="/intelligence", tags=["Intelligence Cards"])

@router.get("/card/{entity_id}", response_model=IntelligenceCardResponse)
def get_entity_card(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the intelligence card for a resolved entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    graph = _build_graph_for_entity(entity, db)
    generator = IntelligenceCardGenerator()
    entity_meta = {
        "type": entity.entity_type or "organization",
        "canonical": entity.canonical_name,
        "wikidata_qid": entity.wikidata_id,
        "description": entity.description or f"Profile for {entity.canonical_name}"
    }
    
    card = generator.generate_from_graph(
        entity_name=entity.canonical_name,
        entity_meta=entity_meta,
        evidence_graph=graph,
        vertical="company"
    )
    return card.to_dict()

@router.post("/card/{entity_id}/refresh", response_model=IntelligenceCardResponse)
def refresh_entity_card(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recompile and refresh the intelligence card for an entity."""
    return get_entity_card(entity_id, db, current_user)

@router.get("/summary/{entity_id}", response_model=SynthesisResponse)
async def get_entity_summary(
    entity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a synthesized markdown summary with citations for an entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    links = db.query(EntityLink).filter(EntityLink.entity_id == entity.id).all()
    documents = []
    for link in links:
        result = db.query(NormalizedResult).filter(NormalizedResult.id == link.result_id).first()
        if result:
            documents.append({
                "title": result.title,
                "url": result.url,
                "snippet": result.snippet or "No content snippet",
                "source": result.source
            })
            
    synthesis_service = SynthesisService()
    synthesis_out = await synthesis_service.synthesize(
        query=f"Provide a summary of {entity.canonical_name}",
        documents=documents,
        vertical="company"
    )
    
    return SynthesisResponse(
        summary=synthesis_out.summary,
        citations={
            k: {
                "citation_id": v.citation_id,
                "title": v.title,
                "url": v.url,
                "source": v.source
            }
            for k, v in synthesis_out.citations.items()
        },
        confidence_score=synthesis_out.confidence_score
    )
