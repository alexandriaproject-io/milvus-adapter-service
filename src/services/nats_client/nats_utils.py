import time
import asyncio
from src.config import config
from logger import log
from src.utils import thrift_to_binary


async def send_reply(nc, reply, thrift_obj):
    if reply:
        try:
            await nc.publish(reply, thrift_to_binary(thrift_obj))
        except TimeoutError as e:
            log.error(f"Request client timed-out: {e}")
        except Exception as e:
            log.error(f"Error in publishing response: {e}")


async def keep_alive(nc, shared_stats, execution_queue, check_milvus_health):
    # not breaking maybe nats will reconnect properly. k8s will kill the process on its own
    timer = time.perf_counter() - 5
    while True:
        await asyncio.sleep(0.001)  # keep it running
        if time.perf_counter() - timer > 5:
            try:
                await check_milvus_health(execution_queue=execution_queue, shared_stats=shared_stats)

                response = await nc.request(f"milvus.health.{config.NATS_SUFFIX}", b'health-check', timeout=1)
                # expect properly formed response
                if response.data.decode() == 'yes':
                    shared_stats["nats-alive"] = True
                    # Ready only sets once when service starts and is ignored by k8s afterward so no need to un-set it
                    if not shared_stats["nats-ready"]:
                        shared_stats["nats-ready"] = True
                else:
                    shared_stats["nats-alive"] = False
                    log.error("Mismatch health response.")

            except TimeoutError:
                shared_stats["nats-alive"] = False
                log.error("Health request timed out.")
                # Nats is finicky about loss of connection so we close it and kill the service
                execution_queue.put(None)
                await nc.close()
                break
            except Exception as e:
                shared_stats["nats-alive"] = False
                log.error("Error: %s", e)
                # Nats is finicky about loss of connection so we close it and kill the service
                execution_queue.put(None)
                await nc.close()
                break
            finally:
                timer = time.perf_counter()
