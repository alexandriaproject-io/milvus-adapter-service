from multiprocessing import Process, Manager
from src.internal_services import run_services
import sys

if __name__ == '__main__':
    try:
        manager = Manager()
        shared_stats = manager.dict()
        com_server = Process(target=run_services, args=(shared_stats,), daemon=True)
        com_server.start()
        com_server.join()
    except KeyboardInterrupt:
        print("Interrupt received, shutting down...")
        com_server.terminate()  # Terminate the subprocess
        com_server.join()  # Wait for the subprocess to terminate
        print("Goodbye...")
        sys.exit(0)  # Exit the program
