import uvicorn
from fastapi import FastAPI, Request
from src.logger import log
from src.config import config
from src.services.api_server.search_controller import handle_search, MilvusSegmentGetRequest, SearchResponse
from src.services.api_server.upsert_controller import handle_upsert, UpsertRequest, UpsertResponse

app = FastAPI(title='Milvus Adapter Service', description='Rest API', version='1.0', docs_url='/swagger')


@app.post('/api/search', response_model=SearchResponse)
async def search_items(request: Request, payload: MilvusSegmentGetRequest):
    global execution_queue
    data = payload.dict(exclude_none=True)
    return await handle_search(data, execution_queue)


@app.post('/api/upsert', response_model=UpsertResponse)
async def search_items(request: Request, payload: UpsertRequest):
    global execution_queue
    data = payload.dict(exclude_none=True)
    return await handle_upsert(data, execution_queue)


@app.on_event("startup")
async def startup_event():
    global ready_event
    ready_event.set()


def run_fastapi_app(queue, event):
    global execution_queue
    global ready_event
    execution_queue = queue
    ready_event = event
    uvicorn.run(app, host=config.API_SERVER_HOST, port=config.API_SERVER_PORT, log_level="error")
