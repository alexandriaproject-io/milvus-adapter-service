import asyncio
import ssl
import time
import base64
from logger import log
from src.config import config
from nats.aio.client import Client as NATS
import atexit


async def handle_future_and_publish(reply, future):
    # Wait for the future to be resolved
    start = time.perf_counter()
    response = await future
    # Once resolved, publish the response if a reply subject is provided
    if reply:
        try:
            response_bytes = response.cpu().numpy().tobytes()
            await nc.publish(reply, base64.b64encode(response_bytes))
        except TimeoutError as e:
            log.error(f"Request client timed-out: {e}")
        except Exception as e:
            log.error(f"Error in publishing response: {e}")

    log.debug(f"handle_future_and_publish execution time:{time.perf_counter() - start}")


async def handle_health_future(future):
    global shared_stats
    response = await future
    shared_stats["milvus-alive"] = response


async def handle_add(msg):
    global execution_queue
    global nc
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    log.debug(f"Received a message on '{subject} {reply}': {data}")

    future = asyncio.Future()
    execution_queue.put(({
                             "msg_type": "upsert",
                             "query": {
                                 "document_ids": None,
                                 "search": "Add operation completed"
                             }
                         }, future))
    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_future_and_publish(reply, future))


async def handle_get(msg):
    global execution_queue
    global nc
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    log.debug(f"Received a message on '{subject} {reply}': {data}")

    future = asyncio.Future()
    execution_queue.put(({
                             "msg_type": "search",
                             "query": {
                                 "document_ids": None,
                                 "search": "Get operation result"
                             }
                         }, future))

    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_future_and_publish(reply, future))


async def check_milvus_health():
    global execution_queue
    future = asyncio.Future()
    execution_queue.put(({"msg_type": "health"}, future))
    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_health_future(future))


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

    await js.add_stream(name="milvus_adapter", subjects=[f"milvus.add", f"milvus.add.{config.NATS_SUFFIX}"])

    await js.subscribe(subject=f"milvus.add", queue=config.NATS_QUEUE_GROUP, cb=handle_add)
    await js.subscribe(subject=f"milvus.add.{config.NATS_SUFFIX}", queue=config.NATS_QUEUE_GROUP, cb=handle_add)

    await nc.subscribe(subject=f"milvus.get", queue=config.NATS_QUEUE_GROUP, cb=handle_get)
    await nc.subscribe(subject=f"milvus.get.{config.NATS_SUFFIX}", queue=config.NATS_QUEUE_GROUP, cb=handle_get)

    await nc.subscribe(subject=f"milvus.health", queue=config.NATS_QUEUE_GROUP, cb=help_health)
    await nc.subscribe(subject=f"milvus.health.{config.NATS_SUFFIX}", queue=config.NATS_QUEUE_GROUP, cb=help_health)
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
                # send health request to nats to check connection, there is no reason to await this.
                check_milvus_health()

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
