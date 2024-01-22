import asyncio
import time
from logger import log
from src.utils import thrift_read
from src.services.nats_client.nats_utils import send_reply
from com.milvus.nats.ttypes import (
    MilvusSegmentGetRequest,
    L2SegmentSearchResponse,
    L2SegmentSearchResult,
)


async def handle_get_future(nc, reply, future):
    start = time.perf_counter()
    results = await future
    if reply:
        record = L2SegmentSearchResponse()
        record.results = []
        if results.get("error", None):
            record.total = 0
            record.is_error = True
            record.error_text = results.get("error", "Unknown error")
        else:
            record.is_error = False
            result_items = results.get("items", [])
            record.total = len(result_items)
            for result in result_items:
                ids = result.get("id", "::").split(":")
                record.results.append(L2SegmentSearchResult(
                    distance=result.get("distance", 0),
                    document_id=ids[0],
                    section_id=ids[1] if len(ids) > 1 else '',
                    segment_id=ids[2] if len(ids) > 2 else '',
                ))
        await send_reply(nc, reply, record)
    log.debug(f"handle_get_future execution time: {time.perf_counter() - start}")


async def handle_get(msg, nc, execution_queue):
    subject = msg.subject
    reply = msg.reply
    record = thrift_read(msg.data, MilvusSegmentGetRequest)
    if record:
        log.debug(f"Received a message on '{subject} {reply}'")
        future = asyncio.Future()
        execution_queue.put(({
                                 "msg_type": "search",
                                 "query": {
                                     "search": record.search,
                                     "document_ids": record.document_ids,
                                     "offset": record.offset,
                                     "limit": record.limit,
                                     "sf": record.sf,
                                 }
                             }, future))
        # Not awaiting here on purpose to not block this loop
        asyncio.create_task(handle_get_future(nc, reply, future))
