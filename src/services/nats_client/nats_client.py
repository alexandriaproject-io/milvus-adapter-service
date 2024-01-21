import asyncio
import ssl
import time
import base64
import atexit
from logger import log
from src.config import config
from nats.aio.client import Client as NATS
from com.milvus.nats.ttypes import (
    MilvusSegmentGetRequest,
    MilvusSegmentUpsertPayload,
    MilvusSegmentDeletePayload,
    L2SegmentSearchResponse,
    L2SegmentSearchResult,
    L2SegmentUpsertResponse,
    L2SegmentDeleteResponse
)
from src.utils import thrift_read, thrift_to_binary


async def handle_health_future(future):
    global shared_stats
    response = await future
    shared_stats["milvus-alive"] = response


async def check_milvus_health():
    global execution_queue
    future = asyncio.Future()
    execution_queue.put(({"msg_type": "health"}, future))
    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_health_future(future))


async def send_reply(reply, thrift_obj):
    if reply:
        try:
            await nc.publish(reply, thrift_to_binary(thrift_obj))
        except TimeoutError as e:
            log.error(f"Request client timed-out: {e}")
        except Exception as e:
            log.error(f"Error in publishing response: {e}")


async def handle_get_future(reply, future):
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
        await send_reply(reply, record)
    log.debug(f"handle_get_future execution time: {time.perf_counter() - start}")


async def handle_get(msg):
    global execution_queue
    global nc
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
        asyncio.create_task(handle_get_future(reply, future))


async def handle_add_future(reply, future):
    start = time.perf_counter()
    results = await future
    if reply:
        record = L2SegmentUpsertResponse()
        if results.get("error", None):
            record.is_error = True
            record.error_text = results.get("error", "Unknown error")
            record.insert_count = 0
            record.update_count = 0
            record.delete_count = 0
        else:
            record.is_error = False
            record.insert_count = results.get("insert_count", 0)
            record.update_count = results.get("upsert_count", 0)
            record.delete_count = results.get("delete_count", 0)
        await send_reply(reply, record)
    log.debug(f"handle_add_future execution time: {time.perf_counter() - start}")


async def handle_add(msg):
    global execution_queue
    global nc
    subject = msg.subject
    reply = msg.reply
    record = thrift_read(msg.data, MilvusSegmentUpsertPayload)
    if record:
        log.debug(f"Received a message on '{subject} {reply}'")
        future = asyncio.Future()
        execution_queue.put(({
                                 "msg_type": "upsert",
                                 "query": {
                                     "text": record.segment_text,
                                     "document_id": record.document_id,
                                     "section_id": record.section_id,
                                     "segment_id": record.segment_id,
                                 }
                             }, future))
        # Not awaiting here on purpose to not block this loop
        asyncio.create_task(handle_add_future(reply, future))


async def handle_delete_future(reply, future):
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
        await send_reply(reply, record)
    log.debug(f"handle_delete_future execution time: {time.perf_counter() - start}")


async def handle_delete(msg):
    global execution_queue
    global nc
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
        asyncio.create_task(handle_delete_future(reply, future))


async def help_health(msg):
    global nc
    await nc.publish(msg.reply, b'yes')


def cleanup():
    print("Closing nats connection.")
    global nc
    nc.close()
    time.sleep(config.NATS_GRACE_TIME)


async def start_nats_client(stats, executions, nats_ready_event):
    global shared_stats
    global execution_queue
    global nc

    shared_stats = stats
    execution_queue = executions
    nc = NATS()

    # Configure TLS context
    tls_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

    # Connect to NATS server with username, password, and TLS
    await nc.connect(
        config.NATS_URL,
        user=config.NATS_USER,
        password=config.NATS_PASS,
        tls=tls_context if config.NATS_TLS else None,
        allow_reconnect=False,
    )
    atexit.register(cleanup)

    js = nc.jetstream()

    # await js.delete_stream(name="milvus_adapter")
    # await js.add_stream(name="milvus_adapter", subjects=[
    await js.update_stream(name="milvus_adapter", subjects=[
        f"milvus.js.add",
        f"milvus.js.add.{config.NATS_SUFFIX}",
        f"milvus.js.del",
        f"milvus.js.del.{config.NATS_SUFFIX}"
    ])

    # Milvus ADD js and request-reply
    await js.subscribe(subject=f"milvus.js.add", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=handle_add)
    await js.subscribe(subject=f"milvus.js.add.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=handle_add)
    await nc.subscribe(subject=f"milvus.add", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=handle_add)
    await nc.subscribe(subject=f"milvus.add.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=handle_add)

    # Milvus DELETE js and request-reply
    await js.subscribe(subject=f"milvus.js.del", queue=f"{config.NATS_QUEUE_GROUP}-del", cb=handle_delete)
    await js.subscribe(subject=f"milvus.js.del.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-del",
                       cb=handle_delete)

    await nc.subscribe(subject=f"milvus.del", queue=f"{config.NATS_QUEUE_GROUP}-del", cb=handle_delete)
    await nc.subscribe(subject=f"milvus.del.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-del",
                       cb=handle_delete)

    # Milvus GET request reply
    await nc.subscribe(subject=f"milvus.get", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=handle_get)
    await nc.subscribe(subject=f"milvus.get.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=handle_get)

    # Milvus HEALTH request reply
    await nc.subscribe(subject=f"milvus.health", queue=f"{config.NATS_QUEUE_GROUP}-health", cb=help_health)
    await nc.subscribe(subject=f"milvus.health.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-health",
                       cb=help_health)
    log.info("Listening for messages on 'milvus.add', 'milvus.get' and 'milvus.health' subjects...")

    nats_ready_event.set()
    await keep_alive()


async def keep_alive():
    global shared_stats
    # not breaking maybe nats will reconnect properly. k8s will kill the process on its own
    timer = time.perf_counter() - 5
    while True:
        await asyncio.sleep(0.001)  # keep it running
        if time.perf_counter() - timer > 5:
            try:
                await check_milvus_health()

                response = await nc.request(f"milvus.health.{config.NATS_SUFFIX}", b'health-check', timeout=1)
                # expect properly formed response
                if response.data.decode() == 'yes':
                    shared_stats["nats-alive"] = True
                    # Ready only sets once when service starts and is ignored by k8s afterward so no need to un-set it
                    if not shared_stats["nats-ready"]:
                        shared_stats["nats-ready"] = True
                else:
                    shared_stats["nats-alive"] = False
                    log.error("Mismatch health response.")

            except TimeoutError:
                shared_stats["nats-alive"] = False
                log.error("Health request timed out.")
                # Nats is finicky about loss of connection so we close it and kill the service
                execution_queue.put(None)
                await nc.close()
                break
            except Exception as e:
                shared_stats["nats-alive"] = False
                log.error("Error: %s", e)
                # Nats is finicky about loss of connection so we close it and kill the service
                execution_queue.put(None)
                await nc.close()
                break
            finally:
                timer = time.perf_counter()
