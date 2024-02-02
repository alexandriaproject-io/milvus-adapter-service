from multiprocessing import Manager
import queue
import threading
import asyncio
from src.logger import log
from src.config import config
from src.services.status_server import status_server
from src.services.milvus_service import milvus_service
from src.services.nats_client import nats_client
from src.services.api_server import api_server

if __name__ == '__main__':
    execution_queue = queue.Queue()
    startup_queue = queue.Queue()
    shared_stats = {
        "nats-ready": not config.NATS_ENABLED,
        "nats-alive": not config.NATS_ENABLED,
        "milvus-ready": False,
        "milvus-alive": False
    }


    def shutdown_services(servie_name):
        log.error(f"Service{servie_name} requested shutdown")
        exit(1)


    for i in range(config.MILVUS_WORKERS):
        log.info(f"Starting Milvus worker #{i + 1}")
        milvus_thread = threading.Thread(
            target=milvus_service.start_milvus_service,
            args=(shared_stats, execution_queue, startup_queue, i,),
            daemon=True
        )
        milvus_thread.start()
        log.info(f"Waiting for Milvus worker #{i + 1} to be ready")
        thread_status = startup_queue.get()
        if not thread_status.get("success", False):
            log.error(thread_status.get("error", "Unknown error"))
            exit(1)

    if config.NATS_ENABLED:
        # Run the NATS client asynchronously
        log.info("Starting Nats client")

        asyncio_thread = threading.Thread(
            target=asyncio.run,
            args=(nats_client.start_nats_client(shared_stats, execution_queue, startup_queue),),
            daemon=True
        )
        asyncio_thread.start()
        log.info("Waiting for nats to be ready")
        thread_status = startup_queue.get()
        if not thread_status.get("success", False):
            log.error(thread_status.get("error", "Unknown error"))
            exit(1)

    if config.API_SERVER_ENABLED:
        # Run the Rest API server asynchronously
        log.info("Starting API server")
        api_ready_event = threading.Event()
        asyncio_thread = threading.Thread(
            target=api_server.run_fastapi_app,
            args=(execution_queue, api_ready_event,),
            daemon=True
        )
        asyncio_thread.start()
        log.info("Waiting for API server to start")
        api_ready_event.wait()

    # Run the Flask app in a separate thread
    log.info("Starting Status server")
    status_server.run_flask_app(shared_stats)
