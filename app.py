#!/usr/bin/env python

"""
Example of a painfully trivial Flask application without setting up uWSGI, and
otherwise doing dumb things
"""

import boto3
import logging
import json_logging
import MySQLdb
import os
import redis
import socket
import time
import traceback
import sys
from fortunate import Fortunate
from flask import Flask, jsonify


app = Flask(__name__)
json_logging.ENABLE_JSON_LOGGING = True
json_logging.init(framework_name='flask')
json_logging.init_request_instrument(app)
logger = logging.getLogger("test-logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


ssm_client = boto3.client('ssm')
REDIS_HOST = ssm_client.get_parameter(Name=os.getenv('REDIS_HOST_PARAMETER'), WithDecryption=False)['Parameter']['Value']
AURORA_HOST = ssm_client.get_parameter(Name=os.getenv('AURORA_HOST_PARAMETER'), WithDecryption=False)['Parameter']['Value']
AURORA_PASSWORD = ssm_client.get_parameter(Name=os.getenv('AURORA_PASSWORD_PARAMETER'), WithDecryption=False)['Parameter']['Value']
AURORA_DB = ssm_client.get_parameter(Name=os.getenv('AURORA_DB_PARAMETER'), WithDecryption=False)['Parameter']['Value']
AURORA_USER = ssm_client.get_parameter(Name=os.getenv('AURORA_USER_PARAMETER'), WithDecryption=False)['Parameter']['Value']


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


class Aurora(object):
    """Base class for Aurora handling"""
    
    def __init__(self):
        self.db = MySQLdb.connect(host=AURORA_HOST, user=AURORA_USER, passwd=AURORA_PASSWORD, db=AURORA_DB, connect_timeout=2, autocommit=True)
        
    def health_check(self):
        """Check if Aurora is reachable"""
        try:
            cur = self.db.cursor()
            cur.execute('select now()')
            results = cur.fetchone()
            cur.close()
            return True
        except:
            return False
        
    def insert_notes(self, text):
        """Inserts arbitrary notes into the hits table"""
        generator = Fortunate('/usr/share/games/fortune/startrek')
        cur = self.db.cursor()
        cur.execute('insert into hits (notes) values (%s)' % MySQLdb.string_literal(generator()))
        cur.close()
        
    def close(self):
        """Closes the DB connection"""
        self.db.close()


@app.route('/')
def index():
    db = DB()
    last = db.get_time()
    db.set_time()
    return jsonify({'last_hit': last})
    # return jsonify({'last_hit': last, 'message': 'Live long and prosper'})


@app.route('/health_check')
def health_check():
    db = DB()
    aurora = Aurora()
    if db.health_check() is True and aurora.health_check() is True:
        aurora.insert_notes('asdf asdf asdf')
        aurora.close()
        return jsonify({'status': 'ok', 'backend': socket.gethostname(), 'message': 'Live long and prosper'}), 200
        # return jsonify({'status': 'ok', 'backend': socket.gethostname()}), 200
    else:
        aurora.close()
        return jsonify({'status': 'unavailable', 'backend': socket.gethostname()}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')
