from src.config import config
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)
from pymilvus.client.constants import ConsistencyLevel

CONNECTION_NAME = "default"


def milvus_connect():
    connections.connect(CONNECTION_NAME,
                        host=config.MILVUS_HOSTNAME,
                        port=config.MILVUS_PORT,
                        user=config.MILVUS_USERNAME,
                        password=config.MILVUS_PASSWORD,
                        secure=config.MILVUS_USE_TLS,
                        )
