import base64
import json
import mimetypes
import os
import random
import tempfile
import time

import magic
import psutil
import yaml

import cherrypy
from cherrypy import log

from outer.emotions import Emotion, emotion_from_str
from service import CoverService


SUPPORTED_EXTENSIONS = {"flac", "mp3", "aiff", "wav", "ogg"}


process = psutil.Process(os.getpid())  # For monitoring purposes

config = yaml.safe_load(open("config.yml"))

service = CoverService(
    config["service"]["protosvg_address"],
    config["service"]["gan_weights"],
    config["service"]["captioner_weights"],
    config["service"]["font_dir"]
)


def base64_encode(img):
    return base64.b64encode(img).decode('utf-8')


def process_generate_request(tmp_filename: str,
                             track_artist: str, track_name: str,
                             emotions: [Emotion]) -> [(str, str)]:
    start = time.time()

    mime = magic.Magic(mime=True)
    ext = mimetypes.guess_extension(mime.from_file(tmp_filename))
    if ext is None:
        os.remove(tmp_filename)
        raise cherrypy.HTTPError(400, message="Unrecognized file format")
    elif ext[1:] not in SUPPORTED_EXTENSIONS:
        os.remove(tmp_filename)
        raise cherrypy.HTTPError(400, message="Unsupported file format")
    else:
        os.rename(tmp_filename, tmp_filename + ext)
        tmp_filename += ext

    result = service.generate(
        tmp_filename, track_artist, track_name, emotions,
        num_samples=5, rasterize=True, watermark=True
    )
    os.remove(tmp_filename)
    result = list(map(lambda x: (x[0], base64_encode(x[1])), result))

    time_spent = time.time() - start
    log("Completed api call.Time spent {0:.3f} s".format(time_spent))

    return result


class ApiServerController(object):
    @cherrypy.expose('/health')
    def health(self):
        result = {
            "status": "OK",  # TODO: when is status not ok?
            "info": {
                "mem": "{0:.3f} MiB".format(process.memory_info().rss / (1024 ** 2)),
                "cpu": process.cpu_percent(),
                "threads": len(process.threads())
            }
        }
        return json.dumps(result).encode("utf-8")

    @cherrypy.expose
    @cherrypy.tools.gzip()
    @cherrypy.tools.json_out()
    def generate(self, audio_file, track_artist: str, track_name: str, emotion: str = None):
        if emotion is None:
            emotion = random.choice(list(Emotion))
        else:
            emotion = emotion_from_str(emotion)
            if emotion is None:
                raise cherrypy.HTTPError(400, message="Incorrect emotion specified")

        track_artist = track_artist[:50]
        track_name = track_name[:70]

        tmp_filename = None
        with tempfile.NamedTemporaryFile(delete=False) as f:
            tmp_filename = f.name
            while True:
                data = audio_file.file.read(8192)
                if not data:
                    break
                f.write(data)

        return process_generate_request(
            tmp_filename,
            track_artist, track_name,
            [emotion]
        )


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
        'tools.response_headers.headers': [
            ('Content-Type', 'application/json;encoding=utf-8')
        ],
    })

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()
