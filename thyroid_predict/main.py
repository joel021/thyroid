#!/usr/bin/env python
#
# deepzoom_multiserver - Example web application for viewing multiple slides
#
# Copyright (c) 2010-2015 Carnegie Mellon University
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of version 2.1 of the GNU Lesser General Public License
# as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
from collections import OrderedDict
from io import BytesIO
import os
from threading import Lock
import openslide
from openslide import OpenSlide, OpenSlideError
from openslide.deepzoom import DeepZoomGenerator
import json
from flask import Flask, abort, make_response, render_template, url_for, request, redirect
import base64
import webbrowser
import subprocess
import sys

if os.name == 'nt':
    _dll_path = os.getenv('OPENSLIDE_PATH')
    if _dll_path is not None:
        if hasattr(os, 'add_dll_directory'):
            # Python >= 3.8
            with os.add_dll_directory(_dll_path):
                import openslide
        else:
            # Python < 3.8
            _orig_path = os.environ.get('PATH', '')
            os.environ['PATH'] = _orig_path + ';' + _dll_path
            import openslide

            os.environ['PATH'] = _orig_path
else:
    import openslide

from user_data import UserData

SLIDE_DIR = '.'
SLIDE_CACHE_SIZE = 10
DEEPZOOM_FORMAT = 'jpeg'
DEEPZOOM_TILE_SIZE = 254
DEEPZOOM_OVERLAP = 1
DEEPZOOM_LIMIT_BOUNDS = True
DEEPZOOM_TILE_QUALITY = 75

class _SlideCache:
    def __init__(self, cache_size, dz_opts):
        self.cache_size = cache_size
        self.dz_opts = dz_opts
        self._lock = Lock()
        self._cache = OrderedDict()

    def get(self, path):
        with self._lock:
            if path in self._cache:
                # Move to end of LRU
                slide = self._cache.pop(path)
                self._cache[path] = slide
                return slide

        osr = OpenSlide(path)
        slide = DeepZoomGenerator(osr, **self.dz_opts)
        try:
            mpp_x = osr.properties[openslide.PROPERTY_NAME_MPP_X]
            mpp_y = osr.properties[openslide.PROPERTY_NAME_MPP_Y]
            slide.mpp = (float(mpp_x) + float(mpp_y)) / 2
        except (KeyError, ValueError):
            slide.mpp = 0

        with self._lock:
            if path not in self._cache:
                if len(self._cache) == self.cache_size:
                    self._cache.popitem(last=False)
                self._cache[path] = slide
        return slide

class _Directory:
    def __init__(self, basedir, relpath=''):
        self.name = os.path.basename(relpath)
        self.children = []
        for name in sorted(os.listdir(os.path.join(basedir, relpath))):
            cur_relpath = os.path.join(relpath, name)
            cur_path = os.path.join(basedir, cur_relpath)
            if os.path.isdir(cur_path):
                cur_dir = _Directory(basedir, cur_relpath)
                if cur_dir.children:
                    self.children.append(cur_dir)
            elif OpenSlide.detect_format(cur_path):
                self.children.append(_SlideFile(cur_relpath))


class _SlideFile:
    def __init__(self, relpath):
        self.name = os.path.basename(relpath)
        self.url_path = relpath

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('DEEPZOOM_MULTISERVER_SETTINGS', silent=True)


@app.before_first_request
def _setup():
    app.basedir = None
    app.configured = False
    app.last_tile_name = None
    app.last_file_name = None

def _get_slide(path):
    app.last_file_name = path
    path = os.path.abspath(os.path.join(app.basedir, path))
    if not path.startswith(app.basedir + os.path.sep):
        # Directory traversal
        abort(404)
    if not os.path.exists(path):
        abort(404)
    try:
        slide = app.cache.get(path)
        slide.filename = os.path.basename(path)
        return slide
    except OpenSlideError:
        abort(404)

"""
@app.route('/')
def index():
    return render_template('files.html', root_dir=_Directory(app.basedir))
"""
@app.route('/')
def index():
    if app.basedir is None:
        return redirect("/main_init")
    
    if not app.configured:
        config_map = {
            'DEEPZOOM_TILE_SIZE': 'tile_size',
            'DEEPZOOM_OVERLAP': 'overlap',
            'DEEPZOOM_LIMIT_BOUNDS': 'limit_bounds',
        }
        opts = {v: app.config[k] for k, v in config_map.items()}
        app.cache = _SlideCache(app.config['SLIDE_CACHE_SIZE'], opts)

        app.configured = True

    return render_template('files.html', root_dir=_Directory(app.basedir))
    
@app.route('/<path:path>')
def slide(path):
    slide = _get_slide(path)
    slide_url = url_for('dzi', path=path)
    return render_template(
        'slide-fullpage.html',
        slide_url=slide_url,
        slide_filename=slide.filename,
        slide_mpp=slide.mpp,
    )

@app.route('/<path:path>.dzi')
def dzi(path):
    slide = _get_slide(path)
    format = app.config['DEEPZOOM_FORMAT']
    resp = make_response(slide.get_dzi(format))
    resp.mimetype = 'application/xml'
    return resp

@app.route('/<path:path>_files/<int:level>/<int:col>_<int:row>.<format>')
def tile(path, level, col, row, format):
    slide = _get_slide(path)
    format = format.lower()
    if format != 'jpeg' and format != 'png':
        # Not supported by Deep Zoom
        abort(404)
    try:
        tile = slide.get_tile(level, (col, row))
    except ValueError:
        # Invalid level or coordinates
        abort(404)
    buf = BytesIO()
    tile.save(buf, format, quality=app.config['DEEPZOOM_TILE_QUALITY'])
    resp = make_response(buf.getvalue())
    resp.mimetype = 'image/%s' % format

    app.last_tile_name = str(level)+"_"+str(col)+"_"+str(row)+"."+format
    return resp

@app.route('/main_init')
def main_init():
    user_data = UserData()
    path_address = request.args.get("path_address")

    if not path_address is None:
        app.basedir = os.path.abspath(path_address)
        return redirect("/")

    return render_template('main_init.html', user_path_list=user_data.load_user_paths())

@app.route('/remove_user_path', methods=['POST'])
def remove_user_path():
    data = request.get_json()
    user_data = UserData()
    return make_response(user_data.remove_path(data['user_path']))

@app.route('/add_user_path', methods=['POST'])
def add_user_path():
    data = request.get_json()
    user_data = UserData()
    return make_response(user_data.save_user_path(data['user_path']))

@app.route('/clear_user_path', methods=['GET'])
def clear_user_paths():
    user_data = UserData()
    user_data.clear()
    return make_response("All user paths was deleted.")

@app.route('/save_print', methods=['GET', 'POST'])
def upload_file():
    
    if request.method == 'POST':
        # check if the post request has the file part
        user_data = UserData(path="/thyroid_user_files/printed_images/"+app.last_file_name[0:app.last_file_name.index(".")])        
        f = open(str(user_data.path)+"/"+app.last_tile_name,"wb")
        f.write(base64.b64decode(request.get_json()['img'].replace('data:image/png;base64,','')))
        f.close()
        return make_response(json.dumps(True))

    return make_response({"result":json.dumps(False), "cause": "method is not POST"})

if sys.platform == 'darwin':
    subprocess.Popen(['open', "http://127.0.0.1:5000"])
else:
    webbrowser.open_new("http://127.0.0.1:5000")

app.run(host="127.0.0.1", port=5000, threaded=True)