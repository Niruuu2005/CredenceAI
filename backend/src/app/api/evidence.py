from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Entity, EntityLink, NormalizedResult, User
from app.services.security import get_current_user
from app.services.evidence_graph import EvidenceGraph, Claim
from app.schemas import EvidenceGraphResponse, ClaimNodeResponse, ClaimEdgeResponse

router = APIRouter(prefix="/evidence", tags=["Evidence Graph"])

def _build_graph_for_entity(entity: Entity, db: Session) -> EvidenceGraph:
    """Helper to dynamically construct the EvidenceGraph for an entity from DB records."""
    graph = EvidenceGraph()
    links = db.query(EntityLink).filter(EntityLink.entity_id == entity.id).all()
    
    for link in links:
        result = db.query(NormalizedResult).filter(NormalizedResult.id == link.result_id).first()
        if result:
            snippet = result.snippet or result.title or "Factual context"
            # Add primary claim
            claim = Claim(
                claim_id=f"c_{result.id[:8]}",
                text=snippet,
                entity=entity.canonical_name,
                source_url=result.url,
                source_reliability=result.quality_scores.final_trust_score if result.quality_scores else 0.8
            )
            graph.add_claim(claim)
            
            # Simple heuristic contradiction detection
            if "not" in snippet.lower() or "deny" in snippet.lower() or "against" in snippet.lower():
                alt_text = f"Alternative statement regarding {entity.canonical_name}: {snippet[:40]}"
                alt_claim = Claim(
                    claim_id=f"c_alt_{result.id[:6]}",
                    text=alt_text,
                    entity=entity.canonical_name,
                    source_url=result.url,
                    source_reliability=0.5
                )
                graph.add_claim(alt_claim)
                graph.add_contradiction(snippet, alt_text, result.url)
    return graph


@router.get("/entities", response_model=List[Dict[str, Any]])
def list_entities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all resolved entities from the database."""
    entities = db.query(Entity).all()
    return [
        {
            "id": ent.id,
            "canonical_name": ent.canonical_name,
            "entity_type": ent.entity_type,
            "wikidata_id": ent.wikidata_id,
            "description": ent.description
        }
        for ent in entities
    ]


@router.get("/entities/{entity_id}/claims", response_model=List[ClaimNodeResponse])
def get_entity_claims(entity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve all claims associated with a specific entity."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    graph = _build_graph_for_entity(entity, db)
    return [n.to_dict() for n in graph.nodes.values()]

@router.get("/claims/{claim_id}", response_model=ClaimNodeResponse)
def get_claim_details(claim_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve details of a single claim by its ID."""
    # Find all entities to search through their dynamic graphs
    entities = db.query(Entity).all()
    for ent in entities:
        graph = _build_graph_for_entity(ent, db)
        if claim_id in graph.nodes:
            return graph.nodes[claim_id].to_dict()
            
    raise HTTPException(status_code=404, detail="Claim not found")

@router.get("/graph/{entity_id}", response_model=EvidenceGraphResponse)
def get_evidence_graph(entity_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Retrieve the full evidence graph for an entity, including nodes, edges, and summary metrics."""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    graph = _build_graph_for_entity(entity, db)
    raw_graph = graph.export()
    
    # Map raw edges keys 'from' to 'from_node' and 'to' to 'to_node'
    mapped_edges = []
    for edge in raw_graph["edges"]:
        mapped_edges.append(ClaimEdgeResponse(
            **{
                "from": edge["from"],
                "to": edge["to"],
                "relationship": edge["relationship"],
                "weight": edge["weight"]
            }
        ))
        
    return EvidenceGraphResponse(
        nodes=raw_graph["nodes"],
        edges=mapped_edges,
        summary=raw_graph["summary"]
    )
