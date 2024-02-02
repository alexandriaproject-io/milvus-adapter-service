import sys
import time
from src.logger import log
from src.config import config
from src.models.vectorizer.model import SentenceModel
from src.services.milvus_service.milvus_db import (
    is_healthy,
    milvus_connect,
    milvus_define_collections,
    upsert_segment,
    search_segments,
    delete_segment,
)


def start_milvus_service(stats, task_queue, startup_queue, worker_id):
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
    try:
        milvus_connect()
    except Exception as e:
        startup_queue.put({"success": False, "error": f"{e}"})
        exit(0)

    log.info(f"Worker #{worker_id}: Verifying collections")
    milvus_define_collections()

    startup_queue.put({"success": True, "error": ""})
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
                upsert_string = segment.get("text", None)
                document_id = segment.get("document_id", None)
                section_id = segment.get("section_id", None)
                segment_id = segment.get("segment_id", None)
                if upsert_string and document_id and section_id and segment_id:
                    vectors = vectorizer.embed_text(upsert_string).cpu().numpy()
                    result = upsert_segment(
                        document_id=document_id,
                        section_id=section_id,
                        segment_id=segment_id,
                        vectors=vectors)
                else:
                    future.set_result({"error": f"Invalid upsert params {segment}"})
            elif msg_type == "search":
                query = task.get("query", {})
                search_string = query.get("search", None)
                if search_string:
                    vectors = vectorizer.embed_text(search_string).cpu().numpy()
                    result = search_segments(
                        query_vectors=vectors,
                        document_ids=query.get("document_ids", None),
                        offset=query.get("offset", None),
                        limit=query.get("limit") or 100,
                        sf=query.get("sf") or 32)
                else:
                    future.set_result({"error": f"Invalid search params {query}"})
            elif msg_type == "delete":
                query = task.get("query", {})
                document_id = query.get("document_id", None)
                section_id = query.get("section_id", None)
                segment_id = query.get("segment_id", None)
                if document_id and section_id and segment_id:
                    result = delete_segment(
                        document_id=document_id,
                        section_id=section_id,
                        segment_id=segment_id)
                else:
                    future.set_result({"error": f"Invalid delete params {query}"})
            else:
                future.set_result({"error": f"Unknown message type: {msg_type}"})
            log.debug(f"Worker #{worker_id}: Task finished in {time.perf_counter() - start}s")
            future.set_result(result)
        except Exception as e:
            log.warn(f"Execution error: {e}")
            future.set_result({"error": f"Execution error: {e}"})
