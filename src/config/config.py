from dotenv import load_dotenv
import os

load_dotenv()

# Log level configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Rest API server configuration
STATUS_SERVER_HOST = os.getenv("STATUS_SERVER_HOST", "0.0.0.0")
STATUS_SERVER_PORT = int(os.getenv("STATUS_SERVER_PORT", "5000"))

# Nats connection configuration
NATS_URL = os.getenv("NATS_URL", "")
NATS_USER = os.getenv("NATS_USER", "")
NATS_PASS = os.getenv("NATS_PASS", "")
NATS_TLS = os.getenv("NATS_TLS", "false").lower() == 'true'
NATS_SUFFIX = os.getenv("NATS_SUFFIX", "default")
NATS_QUEUE_GROUP = os.getenv("NATS_QUEUE_GROUP", None)
NATS_GRACE_TIME = int(os.getenv("NATS_GRACE_TIME", "10"))

MILVUS_HOSTNAME = os.getenv("MILVUS_HOSTNAME", "")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_USERNAME = os.getenv("MILVUS_USERNAME", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")
MILVUS_USE_TLS = os.getenv("MILVUS_USE_TLS", "False").lower() == 'true'
MILVUS_WORKERS = int(os.getenv("MILVUS_WORKERS", "2"))

HUGGING_FACE_AUTH_TOKEN = os.getenv("VECTOR_MODEL_PATH", None)
VECTOR_MODEL_DEVICE = os.getenv("VECTOR_MODEL_DEVICE", None)
VECTOR_MODEL_PATH = os.getenv("VECTOR_MODEL_PATH", "")
VECTOR_MODEL_CACHE_FOLDER = os.getenv("VECTOR_MODEL_CACHE_FOLDER", None)
VECTOR_SEGMENT_COLLECTION = os.getenv("VECTOR_SEGMENT_COLLECTION", "")
VECTOR_DIM = int(os.getenv("VECTOR_DIM", "768"))

INDEX_USE_IVF_FLAT = os.getenv("INDEX_USE_IVF_FLAT", "False").lower() == 'true'
INDEX_USE_HNSW = os.getenv("INDEX_USE_HNSW", "False").lower() == 'true'

NATS_TESTER_USER = os.getenv("NATS_TESTER_USER", "")
NATS_TESTER_PASS = os.getenv("NATS_TESTER_PASS", "")
NATS_TESTER_TLS = os.getenv("NATS_TESTER_TLS", "false").lower() == 'true'

if not NATS_URL or not NATS_USER or not NATS_PASS or not NATS_SUFFIX:
    Exception("Missing nats configurations! Make sure you define NATS_URL,NATS_USER, NATS_PASS and NATS_SUFFIX")
    exit(1)

if not MILVUS_HOSTNAME or not MILVUS_USERNAME or not MILVUS_PASSWORD:
    Exception("Missing milvus configurations! Make sure you define MILVUS_HOSTNAME,MILVUS_USERNAME and MILVUS_PASSWORD")
    exit(1)

if not VECTOR_MODEL_PATH or not VECTOR_SEGMENT_COLLECTION or not NATS_SUFFIX:
    Exception(
        "Missing model configurations! Make sure you define VECTOR_MODEL_PATH,VECTOR_SEGMENT_COLLECTION and NATS_SUFFIX"
    )
    exit(1)

if not INDEX_USE_IVF_FLAT and not INDEX_USE_HNSW:
    Exception("Must set either INDEX_USE_IVF_FLAT=true or INDEX_USE_HNSW=true")
    exit(1)

if INDEX_USE_IVF_FLAT and INDEX_USE_HNSW:
    Exception("Please provide ONLY one index either INDEX_USE_IVF_FLAT or INDEX_USE_HNSW not both.")
    exit(1)
