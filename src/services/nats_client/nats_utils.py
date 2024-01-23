import time
import asyncio
from src.config import config
from src.logger import log
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


async def subscribe_nats_routes(js, nc, routes, help_health, recreate_js=False):
    nc_queue_group = f"{config.NATS_QUEUE_GROUP}-nc"
    js_queue_group = f"{config.NATS_QUEUE_GROUP}-js"
    js_routes = []
    nc_routes = []
    js_subjects = []
    ns_subjects = []
    queues = []
    for route in routes:
        if route.get("jetstream", False):
            queues.append(f"{js_queue_group}-{route['route']}")
            js_subjects += [
                f"milvus.js.{route['route']}",
                f"milvus.js.{route['route']}.{config.NATS_SUFFIX}"
            ]
            js_routes += [
                {"subject": f"milvus.js.{route['route']}",
                 "queue": f"{js_queue_group}-{route['route']}",
                 "handler": route["handler"]},
                {"subject": f"milvus.js.{route['route']}.{config.NATS_SUFFIX}",
                 "queue": f"{js_queue_group}-{route['route']}",
                 "handler": route["handler"]}
            ]
        queues.append(f"{nc_queue_group}-{route['route']}")
        ns_subjects += [
            f"milvus.{route['route']}",
            f"milvus.{route['route']}.{config.NATS_SUFFIX}",
        ]
        nc_routes += [
            {"subject": f"milvus.{route['route']}",
             "queue": f"{nc_queue_group}-{route['route']}",
             "handler": route["handler"]},
            {"subject": f"milvus.{route['route']}.{config.NATS_SUFFIX}",
             "queue": f"{nc_queue_group}-{route['route']}",
             "handler": route["handler"]}
        ]

    log.info(f"Process Nats queues: {sorted(queues)}")
    log.info(f"Listening to Nats subjects: {sorted(ns_subjects)}")
    log.info(f"Listening to Jetstream subjects: {sorted(js_subjects)}")

    if recreate_js:
        await js.delete_stream(name="milvus_adapter")
        await js.add_stream(name="milvus_adapter", subjects=js_subjects)
    else:
        await js.update_stream(name="milvus_adapter", subjects=js_subjects)

    for route in js_routes:
        await js.subscribe(subject=route["subject"], queue=route["queue"], cb=route["handler"])
    for route in nc_routes:
        await nc.subscribe(subject=route["subject"], queue=route["queue"], cb=route["handler"])
    # Milvus HEALTH request reply
    await nc.subscribe(
        subject=f"milvus.health.{config.NATS_SUFFIX}",
        queue=f"{config.NATS_QUEUE_GROUP}-health",
        cb=help_health
    )
