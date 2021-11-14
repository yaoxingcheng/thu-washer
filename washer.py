import argparse
import os
import logging
import requests
import json

from config import TOWER_KEY, DEVICE_KEY

from time import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s', datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def get_results(tower, device):
    logger.info(f"{TOWER_KEY[tower]}, {DEVICE_KEY[device]}")
    payload = f"{{\"towerKey\":\"{TOWER_KEY[tower]}\", \"deviceType\":\"{DEVICE_KEY[device]}\"}}"
    logger.info(payload)
    header = {"Content-Type":"application/json"}
    r = requests.post("https://api.cleverschool.cn/washapi4/device/status", headers=header, data=payload)
    return json.loads(r.text)

def run_washer(port, args):
    app = Flask(__name__, static_folder='./static')
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    CORS(app)
    tower_path = os.path.join(args.sentences_dir, args.tower)
    device_path = os.path.join(args.sentences_dir, args.device)
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/api', methods=['GET'])
    def api():
        tower = request.args['tower']
        device = request.args['device']
        logger.info(f"query: {tower} {device}")
        start = time()
        results = get_results(tower=tower, device=device)
        logger.info(results)
        ret = results["data"]
        if ret is None:
            ret = []
        out = {}
        span = time() - start
        out['ret'] = ret
        out['time'] = "{:.4f}".format(span)
        return jsonify(out)

    @app.route('/files/<path:path>')
    def static_files(path):
        return app.send_static_file('files/' + path)
        
    @app.route('/get_tower', methods=['GET'])
    def get_tower():
        with open(tower_path, 'r') as fp:
            examples = [line.strip() for line in fp.readlines()]
        return jsonify(examples)
    
    @app.route('/get_device', methods=['GET'])
    def get_device():
        with open(device_path, 'r') as fp:
            examples = [line.strip() for line in fp.readlines()]
        return jsonify(examples)
    
    addr = args.ip + ":" + args.port
    logger.info(f'Starting Index server at {addr}')
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sentences_dir', default="./static", type=str)
    parser.add_argument('--tower', default="tower.txt", type=str)
    parser.add_argument('--device', default="device.txt", type=str)
    parser.add_argument('--port', default='8888', type=str)
    parser.add_argument('--ip', default='http://127.0.0.1')
    args = parser.parse_args()
    if "PORT" in os.environ:
        args.port = os.environ["PORT"]
    else:
        args.port = 80
        
    run_washer(args.port, args)