from src.config import config
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)
from pymilvus.client.constants import ConsistencyLevel


def milvus_connect():
    connections.connect("default",
                        host=config.MILVUS_HOSTNAME,
                        port=config.MILVUS_PORT,
                        user=config.MILVUS_USERNAME,
                        password=config.MILVUS_PASSWORD,
                        secure=config.MILVUS_USE_TLS,
                        )

