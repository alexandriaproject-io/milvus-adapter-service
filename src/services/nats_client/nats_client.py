import asyncio
import ssl
import time
import atexit
from logger import log
from src.config import config
from nats.aio.client import Client as NATS
from src.services.nats_client.health_controller import check_milvus_health
from src.services.nats_client.get_controller import handle_get
from src.services.nats_client.add_controller import handle_add
from src.services.nats_client.delete_controller import handle_delete


async def call_get_controller(msg):
    global execution_queue
    global nc
    await handle_get(msg, nc, execution_queue)


async def call_add_controller(msg):
    global execution_queue
    global nc
    await handle_add(msg, nc, execution_queue)


async def call_delete_controller(msg):
    global execution_queue
    global nc
    await handle_delete(msg, nc, execution_queue)


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

    # Do not delete this, used for stream debugging
    # await js.delete_stream(name="milvus_adapter")
    # await js.add_stream(name="milvus_adapter", subjects=[])
    await js.update_stream(name="milvus_adapter", subjects=[
        f"milvus.js.add",
        f"milvus.js.add.{config.NATS_SUFFIX}",
        f"milvus.js.del",
        f"milvus.js.del.{config.NATS_SUFFIX}"
    ])

    # Milvus ADD js and request-reply
    await js.subscribe(subject=f"milvus.js.add", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=call_add_controller)
    await js.subscribe(subject=f"milvus.js.add.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=call_add_controller)
    await nc.subscribe(subject=f"milvus.add", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=call_add_controller)
    await nc.subscribe(subject=f"milvus.add.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=call_add_controller)

    # Milvus DELETE js and request-reply
    await js.subscribe(subject=f"milvus.js.del", queue=f"{config.NATS_QUEUE_GROUP}-del", cb=call_delete_controller)
    await js.subscribe(subject=f"milvus.js.del.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-del",
                       cb=call_delete_controller)

    await nc.subscribe(subject=f"milvus.del", queue=f"{config.NATS_QUEUE_GROUP}-del", cb=call_delete_controller)
    await nc.subscribe(subject=f"milvus.del.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-del",
                       cb=call_delete_controller)

    # Milvus GET request reply
    await nc.subscribe(subject=f"milvus.get", queue=f"{config.NATS_QUEUE_GROUP}-add", cb=call_get_controller)
    await nc.subscribe(subject=f"milvus.get.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-add",
                       cb=call_get_controller)

    # Milvus HEALTH request reply
    await nc.subscribe(subject=f"milvus.health", queue=f"{config.NATS_QUEUE_GROUP}-health", cb=help_health)
    await nc.subscribe(subject=f"milvus.health.{config.NATS_SUFFIX}", queue=f"{config.NATS_QUEUE_GROUP}-health",
                       cb=help_health)
    log.info("Listening for messages on 'milvus.add', 'milvus.get' and 'milvus.health' subjects...")

    nats_ready_event.set()
    await keep_alive()


async def keep_alive():
    global shared_stats
    global execution_queue
    # not breaking maybe nats will reconnect properly. k8s will kill the process on its own
    timer = time.perf_counter() - 5
    while True:
        await asyncio.sleep(0.001)  # keep it running
        if time.perf_counter() - timer > 5:
            try:
                await check_milvus_health(execution_queue=execution_queue, shared_stats=shared_stats)

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
