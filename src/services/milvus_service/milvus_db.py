from src.config import config
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    IndexType
)
from logger import log

CONNECTION_NAME = "default"
VECTOR_FIELD_NAME = "content_embeddings"


def milvus_connect():
    connections.connect(alias=CONNECTION_NAME,
                        host=config.MILVUS_HOSTNAME,
                        port=config.MILVUS_PORT,
                        user=config.MILVUS_USERNAME,
                        password=config.MILVUS_PASSWORD,
                        secure=config.MILVUS_USE_TLS,
                        )


def drop_collection(collection_name):
    if collection_name in utility.list_collections():
        old_collection = Collection(name=collection_name)
        old_collection.drop()


def is_healthy():
    try:
        utility.list_collections(using=CONNECTION_NAME, timeout=5)
        return True
    except Exception as e:
        log.error("Milvus connection timed out")
        return False


def create_segments_collection(collection_name=config.VECTOR_SEGMENT_COLLECTION, dim=config.VECTOR_DIM):
    # Check if collection already exists
    if collection_name in utility.list_collections():
        log.debug(f"Collection {collection_name} already exists.")
        return Collection(name=collection_name)  # Return existing collection

    # Define primary field (segment_id since it's unique)
    vector_id_field = FieldSchema(
        name="segment_id",
        dtype=DataType.VARCHAR,
        is_primary=True,
        description="Document ID:Section ID:Segment ID",
        max_length=255)

    document_id_field = FieldSchema(
        name="document_id",
        dtype=DataType.VARCHAR,
        description="ID of the page that contains the sections",
        is_partition_key=True,
        max_length=255)

    section_id_field = FieldSchema(
        name="section_id",
        dtype=DataType.VARCHAR,
        description="ID of the section that contains the segments",
        max_length=255)

    # Define vector field for content embeddings
    vector_field = FieldSchema(
        name=VECTOR_FIELD_NAME,
        dtype=DataType.FLOAT_VECTOR,
        dim=dim,
        description="Embedding of the confluence section content")

    # Define schema
    schema = CollectionSchema(
        fields=[
            vector_id_field,
            document_id_field,
            section_id_field,
            vector_field
        ],
        description="Embeddings")
    log.info(
        f"Creating collection {collection_name} with vector_id_field,document_id_field,section_id_field,vector_field"
    )
    # Create and return new collection
    collection = Collection(name=collection_name, schema=schema)

    if config.INDEX_USE_IVF_FLAT:
        log.info(f"Creating IVF_FLAT index on vector_field('{VECTOR_FIELD_NAME}')")
        index_params = {
            "metric_type": "L2",
            "index_type": IndexType.IVF_FLAT,
            "params": {"nlist": 256}
        }
        collection.create_index(field_name=VECTOR_FIELD_NAME, index_params=index_params)

    if config.INDEX_USE_HNSW:
        log.info(f"Creating HNSW index on vector_field('{VECTOR_FIELD_NAME}')")
        hnsw_params = {
            "metric_type": "L2",
            "index_type": IndexType.HNSW,
            "params": {"M": 32, "efConstruction": 512}
        }
        collection.create_index(field_name=VECTOR_FIELD_NAME, index_params=hnsw_params)

    return collection


def get_segments_collection(collection_name=config.VECTOR_SEGMENT_COLLECTION):
    # Check if the collection exists
    if collection_name not in utility.list_collections():
        # If not, create a new collection
        return create_segments_collection(collection_name)
    else:
        # If it exists, return the existing collection
        return Collection(name=collection_name)


def upsert_segment(document_id, section_id, segment_id, vectors, collection_name=config.VECTOR_SEGMENT_COLLECTION):
    if not segment_id or not section_id or not document_id or vectors is None or vectors.size == 0:
        raise ValueError("Missing required fields")

    data = [
        [f"{document_id}:{section_id}:{segment_id}"],
        [document_id],
        [section_id],
        [vectors]
    ]

    collection = get_segments_collection(collection_name)
    mr = collection.upsert(data)

    # Return insert results, which might be useful for debugging or validation
    return {
        "upsert_count": mr.upsert_count,
        "insert_count": mr.insert_count,
    }


def search_segments(
        query_vectors,
        limit=100,
        offset=None,
        document_ids=None,
        sf=32,
        collection_name=config.VECTOR_SEGMENT_COLLECTION,
):
    collection = get_segments_collection(collection_name)
    search_params = {
        "metric_type": "L2",
        "params": {
            "ef": sf,       # Specify ef for HNSW index
            "nprobe": sf    # Specify nprobe for IVF_FLAT index
        },
    }

    results = collection.search(
        data=query_vectors,
        anns_field=VECTOR_FIELD_NAME,
        param=search_params,
        limit=limit,
        offset=offset,
        partition_names=document_ids if document_ids and len(document_ids) > 0 else None,
    )
    return results


def delete_item_by_id(collection, item_id):
    log.warn("Removing items may cause performance spikes")
    status = collection.delete(expr=f"id == {item_id}")
    collection.load()
    return status


def milvus_define_collections(re_create=False):
    log.info(f"Collections list: {utility.list_collections()}")
    if re_create:
        drop_collection(config.VECTOR_SEGMENT_COLLECTION)
    create_segments_collection().load()
    return None
