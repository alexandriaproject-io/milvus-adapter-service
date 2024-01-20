import asyncio
from flask import Flask, send_from_directory
from flask_restx import Api, Resource

app = Flask(__name__)
api = Api(app, version='1.0', title='My API', description='A simple API')

# Define a namespace
ns = api.namespace('api', description='Main operations')


# Define resource classes
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
    global shared_stats

    def get(self):
        # Implement stats logic here
        return shared_stats, 200


# Route to serve HTML files
@app.route('/html/<path:filename>')
def serve_html(filename):
    return send_from_directory(app.static_folder, filename)


def run_flask_app(stats):
    global shared_stats
    shared_stats = stats
    app.run(host='0.0.0.0', port=5000, use_reloader=False, )
