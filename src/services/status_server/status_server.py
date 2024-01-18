import asyncio
from flask import Flask
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
    def get(self):
        # Implement stats logic here
        return {
            "request_count": 100,  # Example metric
            "connection_count": 5  # Example metric
        }, 200


def run_flask_app(stats):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    global shared_stats
    shared_stats = stats
    app.run(host='0.0.0.0', port=5000, use_reloader=False, )
