import asyncio
import time
from src.logger import log
from fastapi import HTTPException
from pydantic import BaseModel


class DeleteRequest(BaseModel):
    document_id: str
    section_id: str
    segment_id: str


class DeleteResponse(BaseModel):
    delete_count: int


def validate_milvus_segment_delete_payload(data):
    errors = []

    required_fields = ['document_id', 'section_id', 'segment_id']
    for field in required_fields:
        if field not in data:
            errors.append(f'{field} field is required')
        elif not isinstance(data[field], str):
            errors.append(f'{field} must be a string')
        elif not data[field].strip():  # Check for non-empty strings
            errors.append(f'{field} must not be empty')
    return errors


async def handle_delete(data, execution_queue):
    log.debug(f"Entered handle_delete()")
    errors = validate_milvus_segment_delete_payload(data)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    start = time.perf_counter()
    future = asyncio.Future()
    execution_queue.put(({
                             "msg_type": "delete",
                             "query": {
                                 "document_id": data.get("document_id"),
                                 "section_id": data.get("section_id"),
                                 "segment_id": data.get("segment_id"),
                             }
                         }, future))
    response = await future
    if response.get("error", None):
        raise HTTPException(status_code=500, detail={"error": response.get("error", "Unknown error")})

    log.debug(f"handle_delete_future execution time: {time.perf_counter() - start}")
    return {
        "delete_count": response.get("delete_count", 0),
    }
