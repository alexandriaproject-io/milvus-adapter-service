import asyncio


async def handle_health_future(future, shared_stats):
    response = await future
    shared_stats["milvus-alive"] = response


async def check_milvus_health(execution_queue, shared_stats):
    future = asyncio.Future()
    execution_queue.put(({"msg_type": "health"}, future))
    # Not awaiting here on purpose to not block this loop
    asyncio.create_task(handle_health_future(future, shared_stats))
