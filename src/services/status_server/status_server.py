from flask import Flask, send_from_directory, redirect, url_for
from flask_restx import Api, Resource
from src.logger import log

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
    log.info("")
    log.info(" * Liveness on http://127.0.0.1:5000/api/alive")
    log.info(" * Readiness on http://127.0.0.1:5000/api/ready")
    log.info(" * Stats on http://127.0.0.1:5000/api/stats")
    log.info("")
    log.info(" * Swagger docs on http://127.0.0.1:5000/swagger")
    log.info(" * Thrift docs on http://127.0.0.1:5000/html")
    log.info("")
    app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=False)
