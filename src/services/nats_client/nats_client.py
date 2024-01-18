import asyncio
import ssl
import time
from src.config import config
from nats.aio.client import Client as NATS


async def handle_future_and_publish(reply, future):
    # Wait for the future to be resolved
    start = time.perf_counter()
    response = await future
    # Once resolved, publish the response if a reply subject is provided
    if reply:
        await nc.publish(reply, response.encode())
    print(f"Execution time:{time.perf_counter() - start}")


async def handle_add(msg):
    global execution_queue
    global nc
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print(f"Received a message on '{subject} {reply}': {data}")

    future = asyncio.Future()
    execution_queue.put(("Add operation completed", future))

    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_future_and_publish(reply, future))


async def handle_get(msg):
    global execution_queue
    global nc
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print(f"Received a message on '{subject} {reply}': {data}")

    future = asyncio.Future()
    execution_queue.put(("Get operation result", future))

    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_future_and_publish(reply, future))


async def help_health(msg):
    global nc
    await nc.publish(msg.reply, b'yes')


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
        tls=tls_context if config.NATS_TLS else None
    )

    await nc.subscribe(subject="milvus.add", cb=handle_add)
    await nc.subscribe(subject="milvus.get", cb=handle_get)

    await nc.subscribe(subject="milvus.health", cb=help_health)
    print("Listening for messages on 'milvus.add' and 'milvus.get' subjects...")

    await keep_alive(nats_ready_event)


async def keep_alive(nats_ready_event):
    global shared_stats
    # not breaking maybe nats will reconnect properly. k8s will kill the process on its own
    timer = time.perf_counter()
    while True:
        await asyncio.sleep(0.001)  # keep it running
        if time.perf_counter() - timer > 10:
            timer = time.perf_counter()
            try:
                # send health request to nats to check connection
                response = await nc.request("milvus.health", b'health-check', timeout=1)
                # expect properly formed response
                if response.data.decode() == 'yes':
                    shared_stats["nats-alive"] = True
                    # Ready only sets once when service starts and is ignored by k8s afterward so no need to un-set it
                    if not shared_stats["nats-ready"]:
                        shared_stats["nats-ready"] = True
                        # tell parent process that nats is ready
                        nats_ready_event.set()
                else:
                    shared_stats["nats-alive"] = False
                    print("Mismatch health response.")
            except TimeoutError:
                shared_stats["nats-alive"] = False
                print("Health request timed out.")
            except Exception as e:
                shared_stats["nats-alive"] = False
                print("Error:", e)
