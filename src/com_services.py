import asyncio
import threading
from src.services.status_server import status_server
from src.services.nats_client import nats_client


def run_com_services(stats):
    global shared_stats
    shared_stats = stats
    shared_stats["nats-ready"] = False
    shared_stats["nats-alive"] = False

    # Run the NATS client asynchronously
    print("Starting Nats client")
    nats_ready_event = threading.Event()
    asyncio_thread = threading.Thread(
        target=asyncio.run,
        args=(nats_client.start_nats_client(shared_stats, nats_ready_event),),
        daemon=True
    )
    asyncio_thread.start()
    print("Waiting for nats to be ready")
    nats_ready_event.wait()
    # Run the Flask app in a separate thread
    print("Starting Status server")
    status_server.run_flask_app(shared_stats)
