from multiprocessing import Manager
import queue
import threading
import asyncio
from src.config import config
from src.services.status_server import status_server
from src.services.nats_client import nats_client
from src.services.milvus_service import milvus_service

if __name__ == '__main__':
    execution_queue = queue.Queue()
    shared_stats = {
        "nats-ready": False,
        "nats-alive": False,
        "milvus-ready": False,
        "milvus-alive": False
    }

    for i in range(config.MILVUS_WORKERS):
        print(f"Starting Milvus worker #{i + 1}")
        milvus_ready_event = threading.Event()
        milvus_thread = threading.Thread(
            target=milvus_service.start_milvus_service,
            args=(shared_stats, execution_queue, milvus_ready_event, i,),
            daemon=True
        )
        milvus_thread.start()
        print(f"Waiting for Milvus worker #{i + 1} to be ready")
        milvus_ready_event.wait()

    # Run the NATS client asynchronously
    print("Starting Nats client")
    nats_ready_event = threading.Event()
    asyncio_thread = threading.Thread(
        target=asyncio.run,
        args=(nats_client.start_nats_client(shared_stats, execution_queue, nats_ready_event),),
        daemon=True
    )
    asyncio_thread.start()
    print("Waiting for nats to be ready")
    nats_ready_event.wait()
    # Run the Flask app in a separate thread
    print("Starting Status server")
    status_server.run_flask_app(shared_stats)
