import asyncio
import ssl
from src.config import config
from nats.aio.client import Client as NATS


async def handle_add(msg, nc):
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print(f"Received a message on '{subject} {reply}': {data}")
    # Async logic for ADD request
    response = "Add operation completed"  # Replace with actual response
    if reply:
        await nc.publish(reply, response.encode())


async def handle_get(msg, nc):
    subject = msg.subject
    reply = msg.reply
    data = msg.data.decode()
    print(f"Received a message on '{subject} {reply}': {data}")
    # Async logic for GET request
    response = "Get operation result"  # Replace with actual response
    if reply:
        await nc.publish(reply, response.encode())


async def help_health(msg, nc):
    await nc.publish(msg.reply, b'yes')


async def start_nats_client(stats, nats_ready_event):
    global shared_stats
    shared_stats = stats

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

    # Define a partial function to include the nc parameter in the callback
    from functools import partial
    add_request = partial(handle_add, nc=nc)
    get_request = partial(handle_get, nc=nc)
    help_request = partial(help_health, nc=nc)

    # Subscribe to subjects with an async message handler
    await nc.subscribe("milvus.health", "workers", help_request)
    await nc.subscribe("milvus.add", "workers", add_request)
    await nc.subscribe("milvus.get", "workers", get_request)

    print("Listening for messages on 'milvus.add' and 'milvus.get' subjects...")

    # not breaking maybe nats will reconnect properly. k8s will kill the process on its own
    while True:
        await asyncio.sleep(1)  # Sleep for 1 second
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
