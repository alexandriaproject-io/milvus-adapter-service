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


NATS_TESTER_USER = os.getenv("NATS_TESTER_USER", "")
NATS_TESTER_PASS = os.getenv("NATS_TESTER_PASS", "")
NATS_TESTER_TLS = os.getenv("NATS_TESTER_TLS", "false").lower() == 'true'

if not NATS_URL or not NATS_USER or not NATS_PASS:
    Exception("Missing nats configurations! Make sure you define NATS_URL,NATS_USER and NATS_PASS")
    exit(1)
