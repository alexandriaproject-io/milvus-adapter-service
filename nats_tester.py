import asyncio
import ssl
import time

from src.config import config
from nats.aio.client import Client as NATS
from nats.errors import TimeoutError
from src.utils import thrift_read, thrift_to_binary
from com.milvus.nats.ttypes import (
    MilvusSegmentUpsertPayload,
    MilvusSegmentGetRequest,
    MilvusSegmentDeletePayload,
    L2SegmentUpsertResponse,
    L2SegmentSearchResponse,
    L2SegmentDeleteResponse
)


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

        start = time.perf_counter()
        payload = MilvusSegmentUpsertPayload(
            segment_text="help me",
            segment_id="segment",
            section_id="section",
            document_id="document"
        )

        response = await nc.request("milvus.add", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentUpsertResponse)
        print(record)

        start = time.perf_counter()
        payload = MilvusSegmentUpsertPayload(
            segment_text="help me 2",
            segment_id="segment2",
            section_id="section2",
            document_id="document2"
        )

        response = await nc.request("milvus.add", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentUpsertResponse)
        print(record)

        start = time.perf_counter()
        payload = MilvusSegmentUpsertPayload(
            segment_text="help me 3",
            segment_id="segment3",
            section_id="section3",
            document_id="document3"
        )

        response = await nc.request("milvus.add", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentUpsertResponse)
        print(record)

        ##############################################
        ##############################################
        ##############################################
        ##############################################

        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=-101,
            document_ids=None
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=["document3", "document2"]
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=["non-existent"]
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        ##################################################
        ##################################################
        ##################################################
        ##################################################
        ##################################################

        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )

        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )
        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        items = record.results
        for item in items:
            start = time.perf_counter()
            payload = MilvusSegmentDeletePayload(
                document_id=item.document_id,
                section_id=item.section_id,
                segment_id=item.segment_id,

            )
            response = await nc.request("milvus.del", thrift_to_binary(payload), timeout=10)

            print(time.perf_counter() - start)
            record = thrift_read(response.data, L2SegmentDeleteResponse)
            print(record)
        #############################################################
        #############################################################
        #############################################################
        #############################################################
        #############################################################

        print("Waiting for milvus to catch up")
        time.sleep(3)
        start = time.perf_counter()
        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)

        #############################################################
        #############################################################
        #############################################################
        #############################################################
        #############################################################
        #############################################################
        print()
        print()
        print()
        print("Testing jetstream")

        payload = MilvusSegmentUpsertPayload(segment_text="help me", segment_id="segment", section_id="section",
                                             document_id="document")

        await nc.publish("milvus.js.add", thrift_to_binary(payload))
        print(f"Adding document_id:document3, section_id:section3, segment_id:segment3")
        payload = MilvusSegmentUpsertPayload(segment_text="help me 2", segment_id="segment2", section_id="section2",
                                             document_id="document2")

        await nc.publish("milvus.js.add", thrift_to_binary(payload))
        print(f"Adding document_id:document3, section_id:section3, segment_id:segment3")
        payload = MilvusSegmentUpsertPayload(segment_text="help me 3", segment_id="segment3", section_id="section3",
                                             document_id="document3")
        print(f"Adding document_id:document3, section_id:section3, segment_id:segment3")
        await nc.publish("milvus.js.add", thrift_to_binary(payload))
        print()
        print("Forcing flashing on nats before sleep blocking")
        await nc.flush()
        time.sleep(1)
        time.sleep(1)
        time.sleep(1)

        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )

        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)
        print()
        items = record.results
        for item in items:
            payload = MilvusSegmentDeletePayload(
                document_id=item.document_id,
                section_id=item.section_id,
                segment_id=item.segment_id,

            )
            await nc.publish("milvus.js.del", thrift_to_binary(payload))
            print(
                f"Deleting document_id:{item.document_id}, section_id:{item.section_id}, segment_id:{item.segment_id}")
        print()
        print("Forcing flashing on nats before sleep blocking")

        await nc.flush()
        time.sleep(3)

        payload = MilvusSegmentGetRequest(
            search="help me",
            sf=33,
            offset=0,
            limit=101,
            document_ids=None
        )
        response = await nc.request("milvus.get", thrift_to_binary(payload), timeout=10)

        print(time.perf_counter() - start)
        record = thrift_read(response.data, L2SegmentSearchResponse)
        print(record)


    except TimeoutError:
        print("Request timed out")

    # Terminate connection to NATS.
    await nc.drain()


if __name__ == '__main__':
    asyncio.run(main())
