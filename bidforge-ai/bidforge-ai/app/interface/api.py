import json

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.container import check_quota, current_tenant, get_graph, get_parser

app = FastAPI(title="BidForge AI", version="1.0")
ALLOWED = {"application/pdf",
           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/v1/tenders/analyze")
async def analyze(file: UploadFile, tenant=Depends(current_tenant), _=Depends(check_quota),
                  graph=Depends(get_graph), parser=Depends(get_parser)):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "PDF or DOCX only")
    text = await parser.parse(await file.read())

    async def events():
        async for step in graph.astream({"tenant_id": tenant.id, "tender_text": text}):
            node, state = next(iter(step.items()))
            yield f"event: {node}\ndata: {json.dumps(state, default=str)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
