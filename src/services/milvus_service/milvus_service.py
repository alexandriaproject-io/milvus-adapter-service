import time
from src.config import config
from src.services.milvus_service.milvus_db import milvus_connect
from src.models.vectorizer.model import SentenceModel
from logger import log


def start_milvus_service(stats, task_queue, milvus_ready_event, worker_id):
    global shared_stats
    global vectorizer
    shared_stats = stats
    log.info("Initializing Sentence Model...")
    vectorizer = SentenceModel(
        model_path=config.VECTOR_MODEL_PATH,
        auth_token=config.HUGGING_FACE_AUTH_TOKEN,
        device=config.VECTOR_MODEL_DEVICE,
        cache_folder=config.VECTOR_MODEL_CACHE_FOLDER,
    )
    vectorizer.load_model()

    log.info("Connecting to Milvus...")
    milvus_connect()
    milvus_ready_event.set()
    shared_stats["milvus-ready"] = True
    shared_stats["milvus-alive"] = True
    while True:
        if task_queue.empty():
            time.sleep(0.001)
            continue
        task, future = task_queue.get()
        if task is None:  # Shutdown signal
            log.info(f"Closing milvus service #{worker_id}")
            task_queue.put(None)
            break
        try:
            log.debug(f"Worker: {worker_id}")
            result = vectorizer.embed_text(task)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
