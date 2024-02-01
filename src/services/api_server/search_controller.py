import asyncio
import time
from src.logger import log
from fastapi import HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    search: str
    document_ids: Optional[List[str]] = None
    offset: Optional[int] = Field(None)
    limit: Optional[int] = Field(None, examples=[100])
    sf: Optional[int] = Field(None, examples=[32])


class SearchResultItem(BaseModel):
    distance: float
    document_id: str
    section_id: str
    segment_id: str


class SearchResponse(BaseModel):
    result_items: int
    results: List[SearchResultItem]


def validate_milvus_segment_get_request(data):
    errors = []
    if 'search' not in data:
        errors.append('search field is required')
    if 'document_ids' in data and not isinstance(data['document_ids'], list):
        errors.append('document_ids must be a list of strings')
    if 'offset' in data:
        if not isinstance(data['offset'], int):
            errors.append('offset must be an integer')
        elif data['offset'] < 0:
            errors.append('offset must be positive')
    if 'limit' in data:
        if not isinstance(data['limit'], int):
            errors.append('limit must be an integer')
        elif data['limit'] < 0:
            errors.append('limit must be positive')
    if 'sf' in data:
        if not isinstance(data['sf'], int):
            errors.append('sf must be an integer')
        elif data['sf'] < 0:
            errors.append('sf must be positive')
    return errors


async def handle_search(data, execution_queue):
    log.debug(f"Entered handle_upsert()")
    errors = validate_milvus_segment_get_request(data)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    start = time.perf_counter()
    future = asyncio.Future()
    execution_queue.put(({
                             "msg_type": "search",
                             "query": {
                                 "search": data.get("search"),
                                 "document_ids": data.get("document_ids"),
                                 "offset": data.get("offset"),
                                 "limit": data.get("limit"),
                                 "sf": data.get("sf"),
                             }
                         }, future))
    response = await future
    if response.get("error", None):
        raise HTTPException(status_code=500, detail={"error": response.get("error", "Unknown error")})

    result_items = response.get("items", [])
    results = []
    for result in result_items:
        ids = result.get("id", "::").split(":")
        results.append({
            "distance": result.get("distance", 0),
            "document_id": ids[0],
            "section_id": ids[1] if len(ids) > 1 else '',
            "segment_id": ids[2] if len(ids) > 2 else '',
        })

    log.debug(f"handle_search_future execution time: {time.perf_counter() - start}")
    return {
        "result_items": len(results),
        "results": results
    }
