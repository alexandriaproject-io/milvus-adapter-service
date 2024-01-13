from multiprocessing import Process, Manager
from src.services.status_server import status_server


if __name__ == '__main__':
    manager = Manager()
    shared_stats = manager.dict()

    status_server = Process(target=status_server.run_flask_app, args=(shared_stats,))
    status_server.start()

    status_server.join()
    print("Starting status server")
