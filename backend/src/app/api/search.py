from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.search_index import SearchIndexClient
from app.services.security import get_current_user
from app.schemas import SearchResponse, SearchResultItem

router = APIRouter(tags=["Search"])

@router.get("/search", response_model=SearchResponse)
def search_internal_index(
    request: Request,
    q: str = Query(None, description="Search query term"),
    mode: str = Query("standard", description="Search execution mode"),
    limit: int = Query(10, description="Max results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trace_id = getattr(request.state, "trace_id", None)
    if not q or not q.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "missing_query", "message": "q parameter is required.", "trace_id": trace_id}
        )
        
    search_client = SearchIndexClient()
    if mode == "hybrid":
        results = search_client.hybrid_search(q, db=db, limit=limit)
    else:
        results = search_client.search(q, db=db, limit=limit)
    

    
    items = []
    for r in results:
        doc = {
            "document_id": r.get("id") or r.get("document_id") or "",
            "job_id": r.get("job_id") or "",
            "url": r.get("url") or "",
            "title": r.get("title") or "",
            "main_text": r.get("snippet") or "",
            "description": r.get("snippet") or "",
            "language": r.get("language") or "en",
            "content_type": "text/html",
            "source": r.get("source") or "",
            "source_type": "web",
            "quality_score": r.get("quality_score") or 1.0,
            "extraction_quality_score": r.get("quality_score") or 1.0,
            "trusted": r.get("decision") == "accept",
            "indexed_at": None,
            "created_at": None,
            "ranking_details": r.get("ranking_details")
        }
        items.append(SearchResultItem(
            title=r.get("title"),
            url=r.get("url"),
            snippet=r.get("snippet"),
            source=r.get("source"),
            score=r.get("quality_score") or r.get("score") or 1.0,
            document=doc
        ))
        
    return SearchResponse(
        query=q,
        results=items,
        total=len(items),
        trace_id=trace_id
    )
