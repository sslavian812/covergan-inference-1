import json
import os
import time
import cherrypy
from cherrypy import log
import yaml

import psutil
process = psutil.Process(os.getpid())  # for monitoring and debugging purposes

config = yaml.safe_load(open("config.yml"))


def process_api_request(body):
    """
    This methos is for extracting json parameters and processing the actual api request.
    All api format and logic is to be kept in here.
    :param body:
    :return:
    """
    payload = body.get('payload')

    start = time.time()
    # ...
    # call you business logic methods here, implement them in different module.
    # ...
    time_spent = time.time() - start
    log("Completed api call.Time spent {0:.3f} s".format(time_spent))

    result = {
        'result': payload
    }
    return json.dumps(result)


class ApiServerController(object):
    @cherrypy.expose('/health')
    def health(self):
        result = {
            "status": "OK",  # TODO when is status not ok?
            "info": {
                "mem": "{0:.3f} MiB".format(process.memory_info().rss / 1024.0 / 1024.0),
                "cpu": process.cpu_percent(),
                "threads": len(process.threads())
            }
        }
        return json.dumps(result).encode("utf-8")

    @cherrypy.expose('/method1')
    def method1(self):
        cl = cherrypy.request.headers['Content-Length']
        raw = cherrypy.request.body.read(int(cl))
        body = json.loads(raw)
        return process_api_request(body).encode("utf-8")


if __name__ == '__main__':
    cherrypy.tree.mount(ApiServerController(), '/')

    cherrypy.config.update({
        'server.socket_port': config["app"]["port"],
        'server.socket_host': config["app"]["host"],
        'server.thread_pool': config["app"]["thread_pool"],
        'log.access_file': "access1.log",
        'log.error_file': "error1.log",
        'log.screen': True,
        'tools.response_headers.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.response_headers.headers': [('Content-Type', 'application/json;encoding=utf-8')],
    })

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()
