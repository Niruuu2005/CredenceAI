import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract X-Trace-ID or generate new one
        trace_id = request.headers.get("x-trace-id") or request.headers.get("X-Trace-Id")
        if not trace_id:
            trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        
        # Attach trace_id to request state so it can be read in endpoints
        request.state.trace_id = trace_id
        
        # Process the request
        response: Response = await call_next(request)
        
        # Attach trace_id to response headers
        response.headers["X-Trace-Id"] = trace_id
        response.headers["x-trace-id"] = trace_id
        return response
