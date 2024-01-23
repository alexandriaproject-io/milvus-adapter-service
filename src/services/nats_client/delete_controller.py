import time
import asyncio
from src.logger import log
from src.utils import thrift_read
from src.services.nats_client.nats_utils import send_reply
from com.milvus.nats.ttypes import (
    MilvusSegmentDeletePayload,
    L2SegmentDeleteResponse
)


async def handle_delete_future(nc, reply, future):
    start = time.perf_counter()
    results = await future
    if reply:
        record = L2SegmentDeleteResponse()
        if results.get("error", None):
            record.is_error = True
            record.error_text = results.get("error", "Unknown error")
            record.delete_count = 0
        else:
            record.is_error = False
            record.delete_count = results.get("delete_count", 0)
        await send_reply(nc, reply, record)
    log.debug(f"handle_delete_future execution time: {time.perf_counter() - start}")


async def handle_delete(msg, nc, execution_queue):
    subject = msg.subject
    reply = msg.reply
    record = thrift_read(msg.data, MilvusSegmentDeletePayload)
    if record:
        log.debug(f"Received a message on '{subject} {reply}'")
        future = asyncio.Future()
        execution_queue.put(({
                                 "msg_type": "delete",
                                 "query": {
                                     "document_id": record.document_id,
                                     "section_id": record.section_id,
                                     "segment_id": record.segment_id,
                                 }
                             }, future))
        # Not awaiting here on purpose to not block this loop
        asyncio.create_task(handle_delete_future(nc, reply, future))
