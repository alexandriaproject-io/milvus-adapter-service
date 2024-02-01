from flask import Flask, send_from_directory, redirect, url_for, jsonify
from flask_restx import Api, Resource
from src.logger import log
from src.config import config

app = Flask(__name__)
api = Api(app, version='1.0', title='Milvus Adapter Service', description='Service health and stats', doc='/swagger')
ns = api.namespace('api', description='Service health and stats')


@ns.route('/ready')
class Ready(Resource):
    def get(self):
        # Implement readiness check logic here
        return {'status': 'ready'}, 200


@ns.route('/alive')
class Alive(Resource):
    def get(self):
        # Implement liveness check logic here
        return {'status': 'alive'}, 200


@ns.route('/stats')
class Stats(Resource):

    def get(self):
        global shared_stats
        # Implement stats logic here
        return shared_stats, 200


@app.route('/html')
def redirect_to_index():
    return redirect('/html/index.html')


@app.route('/html/')
def redirect_to_index_slash():
    return redirect('/html/index.html')


@app.route('/html/<path:filename>')
def serve_html(filename):
    return send_from_directory(app.static_folder, filename or 'index.html')


def run_flask_app(stats):
    global shared_stats
    shared_stats = stats
    log.info(" * ***")
    log.info(f" * Liveness on       http://{config.STATUS_SERVER_HOST}:{config.STATUS_SERVER_PORT}/api/alive")
    log.info(f" * Readiness on      http://{config.STATUS_SERVER_HOST}:{config.STATUS_SERVER_PORT}/api/ready")
    log.info(f" * Stats on          http://{config.STATUS_SERVER_HOST}:{config.STATUS_SERVER_PORT}/api/stats")
    log.info(f" * Status docs on    http://{config.STATUS_SERVER_HOST}:{config.STATUS_SERVER_PORT}/swagger")
    log.info(f" * Thrift docs on    http://{config.STATUS_SERVER_HOST}:{config.STATUS_SERVER_PORT}/html")
    log.info(" * ***")
    if config.API_SERVER_ENABLED:
        log.info(f" * API Swagger on    http://{config.API_SERVER_HOST}:{config.API_SERVER_PORT}/swagger")
        log.info(f" * Rest API on       http://{config.API_SERVER_HOST}:{config.API_SERVER_PORT}/api")
        log.info(" * ***")
    app.run(host=config.STATUS_SERVER_HOST, port=config.STATUS_SERVER_PORT, use_reloader=False, debug=False)
