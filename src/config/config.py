from dotenv import load_dotenv
import os

load_dotenv()

# Log level configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Rest API server configuration
STATUS_SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
STATUS_SERVER_PORT = int(os.getenv("SERVER_PORT", "5050"))

# Nats connection configuration
NATS_URL = os.getenv("NATS_URL", "")
NATS_USER = os.getenv("NATS_USER", "")
NATS_PASS = os.getenv("NATS_PASS", "")
NATS_TLS = os.getenv("NATS_TLS", "false").lower() == 'true'

MILVUS_HOSTNAME = os.getenv("MILVUS_HOSTNAME", "")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_USERNAME = os.getenv("MILVUS_USERNAME", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")
MILVUS_USE_TLS = os.getenv("MILVUS_USE_TLS", "False").lower() == 'true'
MILVUS_WORKERS = int(os.getenv("MILVUS_WORKERS", "2"))

NATS_TESTER_USER = os.getenv("NATS_TESTER_USER", "")
NATS_TESTER_PASS = os.getenv("NATS_TESTER_PASS", "")
NATS_TESTER_TLS = os.getenv("NATS_TESTER_TLS", "false").lower() == 'true'

if not NATS_URL or not NATS_USER or not NATS_PASS:
    Exception("Missing nats configurations! Make sure you define NATS_URL,NATS_USER and NATS_PASS")
    exit(1)

if not MILVUS_HOSTNAME or not MILVUS_USERNAME or not MILVUS_PASSWORD:
    Exception("Missing milvus configurations! Make sure you define MILVUS_HOSTNAME,MILVUS_USERNAME and MILVUS_PASSWORD")
    exit(1)
