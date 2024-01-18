import time
from src.services.milvus_service.milvus_db import milvus_connect


def start_milvus_service(stats, task_queue, milvus_ready_event, worker_id):
    global shared_stats
    shared_stats = stats
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
            print("Closing milvus service, cascade to all workers")
            task_queue.put(None)
            break
        try:
            print(f"Worker executing: {worker_id}")
            start = time.perf_counter()
            time.sleep(1)
            print(f"slept for {time.perf_counter() - start}")
            result = task
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
