import asyncio
import ssl
import time

from src.config import config
from nats.aio.client import Client as NATS
from nats.errors import TimeoutError

async def main():

    nc = NATS()

    # Configure TLS context
    tls_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

    # Connect to NATS server with username, password, and TLS
    print(f"using {config.NATS_TESTER_USER}")
    await nc.connect(
        config.NATS_URL,
        user=config.NATS_TESTER_USER,
        password=config.NATS_TESTER_PASS,
        tls=tls_context if config.NATS_TESTER_TLS else None
    )

    # Send a request and expect a single response
    # and trigger timeout if not faster than 500 ms.
    try:
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        await nc.publish("milvus.add", b'help me')
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.add", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))

        start = time.perf_counter()
        response = await nc.request("milvus.health", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.health", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.health", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.health", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))
        start = time.perf_counter()
        response = await nc.request("milvus.health", b'help me', timeout=10)
        print(time.perf_counter() - start)
        print("Received response: {message}".format(
            message=response.data.decode()))


    except TimeoutError:
        print("Request timed out")


    # Terminate connection to NATS.
    await nc.drain()

if __name__ == '__main__':
    asyncio.run(main())



