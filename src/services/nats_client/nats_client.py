import ssl
import time
import atexit
from src.config import config
from nats.aio.client import Client as NATS
from src.services.nats_client.nats_utils import keep_alive, subscribe_nats_routes
from src.services.nats_client.get_controller import handle_get
from src.services.nats_client.add_controller import handle_add
from src.services.nats_client.delete_controller import handle_delete
from src.services.nats_client.health_controller import check_milvus_health


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


routes = [
    {
        "route": "get",
        "handler": call_get_controller
    },
    {
        "jetstream": True,
        "route": "add",
        "handler": call_add_controller
    },
    {
        "jetstream": True,
        "route": "del",
        "handler": call_delete_controller
    }
]


async def start_nats_client(stats, executions, nats_ready_event):
    global shared_stats
    global execution_queue
    global nc

    shared_stats = stats
    execution_queue = executions
    nc = NATS()

    tls_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    await nc.connect(
        config.NATS_URL,
        user=config.NATS_USER,
        password=config.NATS_PASS,
        tls=tls_context if config.NATS_TLS else None,
        allow_reconnect=False,
    )
    atexit.register(cleanup)
    js = nc.jetstream()

    await subscribe_nats_routes(js, nc, routes, help_health, recreate_js=True)
    nats_ready_event.set()
    await keep_alive(nc, shared_stats, execution_queue, check_milvus_health)


def cleanup():
    global nc
    print("Closing nats connection.")
    nc.close()
    time.sleep(config.NATS_GRACE_TIME)
