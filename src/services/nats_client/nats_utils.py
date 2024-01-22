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
