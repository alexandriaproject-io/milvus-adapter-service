import time
from src.config import config
from src.services.milvus_service.milvus_db import (
    is_healthy,
    milvus_connect,
    milvus_define_collections,
    upsert_segment,
    search_segments,
    delete_segment
)
from src.models.vectorizer.model import SentenceModel
from logger import log


def start_milvus_service(stats, task_queue, milvus_ready_event, worker_id):
    global shared_stats
    global vectorizer
    shared_stats = stats
    log.info(f"Worker #{worker_id}: Initializing Sentence Model...")
    vectorizer = SentenceModel(
        model_path=config.VECTOR_MODEL_PATH,
        auth_token=config.HUGGING_FACE_AUTH_TOKEN,
        device=config.VECTOR_MODEL_DEVICE,
        cache_folder=config.VECTOR_MODEL_CACHE_FOLDER,
    )
    vectorizer.load_model()

    log.info(f"Worker #{worker_id}: Connecting to Milvus...")
    milvus_connect()
    log.info(f"Worker #{worker_id}: Verifying collections")
    milvus_define_collections()

    milvus_ready_event.set()
    shared_stats["milvus-ready"] = True
    shared_stats["milvus-alive"] = True
    while True:
        if task_queue.empty():
            time.sleep(0.001)
            continue
        task_tuple = task_queue.get()
        if task_tuple is None:  # Shutdown signal
            log.info(f"Worker #{worker_id}: Closing milvus service")
            task_queue.put(None)
            break

        task, future = task_tuple
        try:
            msg_type = task.get("msg_type", "unknown")
            if msg_type == 'health':
                future.set_result(is_healthy())
                continue

            log.debug(f"Worker #{worker_id}: Picked up a task {task}")
            start = time.perf_counter()
            result = {"error": f"Unknown message type {msg_type}"}
            if msg_type == "upsert":
                segment = task.get("query", {})
                vectors = vectorizer.embed_text(segment.get("text", "Unknown")).cpu().numpy()
                result = upsert_segment(
                    document_id=segment.get("document_id", None),
                    section_id=segment.get("section_id", None),
                    segment_id=segment.get("segment_id", None),
                    vectors=vectors
                )
            elif msg_type == "search":
                query = task.get("query", {})
                vectors = vectorizer.embed_text(query.get("search", "Unknown")).cpu().numpy()
                result = search_segments(
                    query_vectors=vectors,
                    document_ids=query.get("document_ids", None),
                    offset=query.get("offset", None),
                    limit=query.get("limit", None),
                    sf=query.get("sf", None),
                )
            elif msg_type == "delete":
                query = task.get("query", {})
                result = delete_segment(
                    document_id=query.get("document_id", None),
                    section_id=query.get("section_id", None),
                    segment_id=query.get("segment_id", None),
                )
            log.debug(f"Worker #{worker_id}: Task finished in {time.perf_counter() - start}s")
            future.set_result(result)
        except Exception as e:
            future.set_result({"error": f"Unknown message type: {e}"})
