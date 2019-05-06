#!/usr/bin/env python

"""
Example of a painfully trivial Flask application without setting up uWSGI, and
otherwise doing dumb things
"""

import logging
import json_logging
import os
import redis
import socket
import time
import traceback
import sys
from flask import Flask, jsonify
from logging.config import dictConfig


app = Flask(__name__)
json_logging.ENABLE_JSON_LOGGING = True
json_logging.init(framework_name='flask')
json_logging.init_request_instrument(app)
logger = logging.getLogger("test-logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')


class DB(object):
    """Base class for our Redis shenanigans"""

    def __init__(self):
        self.db = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, socket_timeout=2)

    def set_time(self):
        """Sets a key for the last time this API was hit"""
        self.db.set('last_hit', str(time.time()))

    def get_time(self):
        """Returns the last time this API was previously hit"""
        return str(self.db.get('last_hit'))

    def health_check(self):
        """Checks if Redis is reachable"""
        try:
            self.db.set('health_check', 'ok')
            return True
        except:
            traceback.print_exc()
            return False


@app.route('/')
def index():
    db = DB()
    last = db.get_time()
    db.set_time()
    return jsonify({'last_hit': last})


@app.route('/health_check')
def health_check():
    db = DB()
    if db.health_check() is True:
        return jsonify({'status': 'ok', 'backend': socket.gethostname()}), 200
    else:
        return jsonify({'status': 'unavailable', 'backend': socket.gethostname()}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')
