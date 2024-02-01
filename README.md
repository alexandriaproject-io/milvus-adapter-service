# milvus-adapter-service

The Milvus adapter service simplifies interactions like searching or adding items by vectorizing texts independently,
eliminating the need for using vectors directly. It also integrates NATS.io messaging with Jetstream and employs Thrift
message wrapping for communication with other services.

## Milvus Adapter Service Customization

The service offers customization options including nats subscription modifiers, selection of indexing methods like
IVF_FLAT or HNSW, choice of vectorizing models, and custom collection name. These features enable the service to operate
across multiple deployments, handling diverse data sets such as text or images.
Milvus Adapter Service architecture:

## Table of contents

- [Milvus Adapter Service Architecture](#milvus-adapter-service-architecture)
- [Milvus Adapter Service Flow diagram](#milvus-adapter-service-flow-diagram)
- [Rest API](#rest-api-server)
    - [Rest API Endpoints](#rest-api-endpoints)
- [Status API](#status-api)
- [ENV parameters](#env-parameters)
    - [Status API server configuration](#status-api-server-configuration)
    - [Nats connection configuration](#nats-connection-configuration)
    - [Milvus connection configuration](#milvus-connection-configuration)
    - [Vectorizing configurations](#vectorizing-configurations)
    - [Vectorizer model config](#vectorizer-model-config)
    - [Nats tester config](#nats-tester-config)
- [Run locally](#run-locally)
- [Subscriptions](#subscriptions)
    - [Thrift search request](#thrift-search-request)
    - [Thrift search response](#thrift-search-response)
    - [Thrift add message / request](#thrift-add-message--request)
    - [Thrift add response](#thrift-add-response)
    - [Thrift delete message / request](#thrift-delete-message--request)
    - [Thrift delete response](#thrift-delete-response)

## Milvus Adapter Service Architecture

![Alt text](svgs/Milvus Adapter.drawio.svg)

The Milvus Adapter service orchestrates operations involving data handling and text processing.
It interfaces with a NATS Client to process search, addition, and deletion requests via respective controllers.
The service employs Sentence Transformer Workers for advanced text encoding and decoding for accurate and efficient
linguistic data management.
Tasks are managed through an execution queue and the service is connected to the Milvus DB, ensuring streamlined
operations and communication.

## Rest API Server

When enabled will listen to Rest API requests ( without thrift encoding ):

- Rest API Swagger docs on http://127.0.0.1:5050/swagger
- Rest API will listen on  http://127.0.0.1:5050/api

## Status API

The service exposes status endpoints to allow for easier integration and health monitoring:

- Liveness on http://127.0.0.1:5000/api/alive
- Readiness on http://127.0.0.1:5000/api/ready
- Stats on http://127.0.0.1:5000/api/stats

Additionally, the service will expose swagger and Thrift object documentation at:

- Swagger docs on http://127.0.0.1:5000/swagger
- Thrift docs on http://127.0.0.1:5000/html

## ENV parameters:

### Status server configuration

| **Variable Name** | **Default Value** | **values**                                         | **Description**                                                   |
|-------------------|-------------------|----------------------------------------------------|-------------------------------------------------------------------|
| **LOG_LEVEL**     | info              | critical, fatal, error, warning, warn, info, debug | Level of logs: critical, fatal, error, warning, warn, info, debug |
| **SERVER_HOST**   | 127.0.0.1         | 0.0.0.0 - 255.255.255.255                          | IP address the status server will listen to (0.0.0.0 is any ip).  |
| **SERVER_PORT**   | 5000              | 1-65535                                            | Port the status server will listen to.                            |

### Rest API server configuration

| **Variable Name**      | **Default Value** | **values**                | **Description**                                                    |
|------------------------|-------------------|---------------------------|--------------------------------------------------------------------|
| **API_SERVER_ENABLED** | false             | Bool                      | Weather to enable REST Api server or not                           |
| **API_SERVER_HOST**    | 127.0.0.1         | 0.0.0.0 - 255.255.255.255 | IP address the REST Api server will listen to (0.0.0.0 is any ip). |
| **API_SERVER_PORT**    | 5000              | 1-65535                   | Port the REST Api server will listen to.                           |

### Nats connection configuration

| **Variable Name**    | **Default Value** | **values** | **Description**                                                                  |
|----------------------|-------------------|------------|----------------------------------------------------------------------------------|
| **NATS_ENABLED**     | true              | Bool       | Weather to enable Nats client or not                                             |
| **NATS_URL**         | -                 | Url String | Nats connection url                                                              |
| **NATS_USER**        | -                 | String     | Nats auth user name                                                              |
| **NATS_PASS**        | -                 | String     | Nats auth password                                                               |
| **NATS_TLS**         | False             | Bool       | Weather to use TLS when connecting to nats                                       |
| **NATS_SUFFIX**      | 'default'         | string     | Nats unique subscription suffix, example: milvus.add.{suffix}                    |
| **NATS_QUEUE_GROUP** | -                 | string     | Nats queue group name, usefully when running multiple copies of the same service |
| **NATS_GRACE_TIME**  | 10                | Number     | Time to give the service to finish executing messages when exiting in seconds    |

### Milvus connection configuration

| **Variable Name**   | **Default Value** | **values**      | **Description**                                                |
|---------------------|-------------------|-----------------|----------------------------------------------------------------|
| **MILVUS_HOSTNAME** | -                 | hostname String | Milvus connection url                                          |
| **MILVUS_PORT**     | 19530             | 1-65535         | Milvus connection port                                         |
| **MILVUS_USERNAME** | -                 | String          | Milvus connection user name                                    |
| **MILVUS_PASSWORD** | -                 | String          | Milvus connection password                                     |
| **MILVUS_USE_TLS**  | False             | Bool            | Weather to use TLS when connecting to milvus                   |
| **MILVUS_WORKERS**  | 2                 | Number          | Number of threads to run vectorization and milvus interactions |

### Vectorizing configurations

| **Variable Name**             | **Default Value** | **values** | **Description**                                |
|-------------------------------|-------------------|------------|------------------------------------------------|
| **VECTOR_SEGMENT_COLLECTION** | -                 | String     | Name of the collection                         |
| **VECTOR_DIM**                | 768               | Number     | Number of dimentions in the vector collections |
| **INDEX_USE_IVF_FLAT**        | False             | Bool       | Index collection using IVF_FLAT algorithm      |
| **INDEX_USE_HNSW**            | False             | Bool       | Index collection using HNSW algorithm          |

### Vectorizer model config

| **Variable Name**             | **Default Value** | **values**                                                                                                      | **Description**                                  |
|-------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **VECTOR_MODEL_PATH**         | -                 | String                                                                                                          | Path of the Sentence Transformer model           |
| **VECTOR_MODEL_CACHE_FOLDER** | -                 | String                                                                                                          | Sentence Transformer cache folder                |
| **VECTOR_MODEL_DEVICE**       | cpu               | cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, ort, xla, lazy, vulkan, mps, meta, hpu, mtia | Sentence Transformer model device                |
| **HUGGING_FACE_AUTH_TOKEN**   | -                 | String                                                                                                          | Hugging face token to download restricted models |

### Nats tester config

| **Variable Name**    | **Default Value** | **values** | **Description**                            |
|----------------------|-------------------|------------|--------------------------------------------|
| **NATS_TESTER_USER** | -                 | String     | Nats auth user name                        |
| **NATS_TESTER_PASS** | -                 | String     | Nats auth password                         |
| **NATS_TESTER_TLS**  | False             | Bool       | Weather to use TLS when connecting to nats |

## Run with Docker

`NOTE: The service is built to have external Milvus and Nats.io services`

- With caching ( to avoid re-downloading Sentence transformer models )

```
docker run --env-file .env -v "[YOUR LOCAL CACHE FOLDER]:/cache" --name "milvus-adapter" niftylius/milvus-adapter
```

- Without caching enabled

```
docker run --env-file .env --name "milvus-adapter" niftylius/milvus-adapter
```

## Run locally

- **Create Python Virtual Environment:**
    - `python -m venv venv`
- **Activate the virtual environment:**
    - `source venv/bin/activate`
- **Install required packages:**
    - `pip3 install -r requirements.txt`
- Create `.env` file based on `.env.example`
    - Change the Model path and config then Run the server:
        - `python3 main.py --multiprocess`

## Rest API Endpoints

### POST /api/search

Will return a vector search based on the payload parameters

Payload:

```json
{
  "search": "string",
  // *Required: Search text to find similar items for
  "document_ids": [
    "string"
  ],
  // *Optional: List of document IDs (plays partition role)
  "offset": 0,
  // *Optional: how many responses to skip
  "limit": 0,
  // *Optional: how many responses to return
  "sf": 0
  // *Optional: Search factor ( rf or nprobe depending on the index )
}
```

Response:

```json
{
  "result_items": 0,
  // Results count
  "results": [
    {
      "distance": 0,
      // Distance value
      "document_id": "string",
      // document_id of the result
      "section_id": "string",
      // section_id of the result
      "segment_id": "string"
      // section_id of the result
    }
  ]
}
```

## POST /api/upsert

Will add or update a new vector row/item

Payload:

```json
{
  "segment_text": "string",
  // Text to vectorize and save
  "document_id": "string",
  // Id of the document ( plays partition role )
  "section_id": "string",
  // Id of the section
  "segment_id": "string"
  // Id of the segment
}
```

Response:

```json
{
  "insert_count": 1,
  // Inserted segments
  "upsert_count": 1,
  // Updated segments
  "delete_count": 1
  // Deleted segments
}
```

`NOTE: For some reason they all return as 1 due to an issue with milvus library`

### POST /api/delete

The endpoint will delete the requested vector \
`Warning: Deleting vectors can cause lag spikes and temporary performance slowdowns`

Payload:

```json
{
  "document_id": "string",
  // Id of the document ( plays partition role )
  "section_id": "string",
  // Id of the section
  "segment_id": "string"
  // Id of the segment
}
```

Response:

```json
{
  "delete_count": 1
  // Deleted segments
}
```

## Subscriptions

### Thrift search request

```thrift
struct MilvusSegmentGetRequest {
  1: string search;                         // Search text to find similar items for
  2: optional list<string> document_ids,    // List of document IDs (plays partition role)
  3: optional i16 offset;                   // how many responses to skip
  4: optional i16 limit;                    // how many responses to return
  5: optional i16 sf;                       // Search factor ( rf or nprobe depending on the index )
}
```

### Thrift search response

```thrift
struct L2SegmentSearchResult {
  1: double distance,               // Distance value
  2: string document_id,            // document_id of the result
  3: string section_id,             // section_id of the result
  4: string segment_id              // section_id of the result
}

struct L2SegmentSearchResponse {
  1: list<L2SegmentSearchResult> results,   // List of results
  2: i32 total                              // Results count
  3: bool is_error                          // Is error or not
  4: optional string error_text             // Error message text
}
```

### Thrift add message / request

```thrift
struct MilvusSegmentUpsertPayload {
  1: string segment_text;           // Text to vectorize and save
  2: string document_id;            // Id of the document ( plays partition role )
  3: string section_id;             // Id of the section
  4: string segment_id;             // Id of the segment
}
```

### Thrift add response

```thrift
struct L2SegmentUpsertResponse {
    1: i32 insert_count             // Inserted segments
    2: i32 update_count            // Updated segments
    3: i32 delete_count             // Deleted segments
    4: bool is_error                // Is error or not
    5: optional string error_text   // Error message text
}
```

### Thrift delete message / request

```thrift
struct MilvusSegmentDeletePayload {
  2: string document_id;            // Id of the document ( plays partition role )
  3: string section_id;             // Id of the section
  4: string segment_id;             // Id of the segment
}
```

### Thrift delete response

```thrift
struct L2SegmentDeleteResponse {
    1: i32 delete_count             // Deleted segments
    3: bool is_error                // Is error or not
    4: optional string error_text   // Error message text
}
```
