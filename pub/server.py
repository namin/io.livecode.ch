from flask import Flask
from flask import request
from flask import render_template
from flask import render_template_string
from flask import jsonify
from flask import json
from jinja2.exceptions import TemplateSyntaxError

import os

import cfg
DEBUG = False
SERVER_NAME = 'io.livecode.ch'
DKR_BASE_IMAGE = 'namin/io.livecode.ch'
DKR_IMAGE_PREFIX = 'temp/io.livecode.ch'
SNIPPET_TMP_DIR = '/tmp/snippets'

app = Flask(__name__)
if not os.path.exists(SNIPPET_TMP_DIR):
    os.makedirs(SNIPPET_TMP_DIR)
github_bot_token = os.environ.get('GITHUB_BOT_TOKEN', None)
github_headers = {'Authorization':'token ' + github_bot_token, 'Accept': 'application/vnd.github.v3+json'}

from redis import Redis
redis = Redis()

import docker

import hashlib
import re

import requests
import base64
import json

def dkr_base_img():
    return DKR_BASE_IMAGE

def dkr_client():
    return docker.from_env()

def dkr_already_installed(img, c=None):
    c = c or dkr_client()
    try:
        c.images.get(img)
    except docker.errors.ImageNotFound:
        return False
    return True

def dkr_check_img(img, git_url, refresh=False, suffix="", user=None, repo=None, clone_recursive=None):
    recursive = "--recursive" if clone_recursive is None or clone_recursive  else ""
    c = dkr_client()
    if refresh:
        redis.delete(img)
    if not refresh and dkr_already_installed(img, c):
        return {'status':0, 'out':'already installed'}
    if suffix != "":
        suffix = "-"+suffix
    base_image = dkr_base_img()+suffix
    try:
        c.images.get(base_image)
    except docker.errors.ImageNotFound:
        return {'status':1, 'out':'base image %s does not exists' % base_image}
    m = c.containers.create(base_image, 'git clone %s "%s" /home/runner/code' % (recursive, git_url), user='runner')
    m.start()
    s = m.wait()['StatusCode']
    if s!=0:
        return {'status':s, 'out':'error cloning repository %s' % git_url}
    m.commit(img)
    return dkr_run(img, 'livecode-install', img, c=c, timeout=100000)

def dkr_run(img, cmd, commit=None, timeout=500, c=None):
    c = c or dkr_client()
    r = ""
    m = c.containers.create(img,
                            "timeout %d %s" % (timeout, cmd),
                            user='runner',
                            environment={'HOME':'/home/runner'},
                            volumes={SNIPPET_TMP_DIR: {'bind': '/mnt/snippets', 'mode':'ro'}},
                            network_disabled=False)
    m.start()
    s = m.wait()['StatusCode']
    if s!=0:
        r += "error: (%d)\n" % s
    if s==137:
        r += "killed!"
    elif s==125:
        r += "timeout!"
    elif s==124:
        r += "inifinite loop!"
    else:
        r += m.logs().decode('utf-8')
    if commit:
        m.commit(repository=commit)
    return {'status':s, 'out':r}

def github_dkr_img(user, repo, suffix):
    if suffix != "":
        suffix = "/"+suffix
    return ('%s/github.com/%s/%s%s' % (DKR_IMAGE_PREFIX, user, repo, suffix)).lower()

def github_check_url(user, repo):
    return 'https://github.com/%s/%s' % (user, repo)

def github_git_url(user, repo):
    return 'https://github.com/%s/%s.git' % (user, repo)

def github_defaults_url(user, repo):
    return 'https://api.github.com/repos/%s/%s/contents/.io.livecode.ch/defaults.json' % (user, repo)

def github_site_index_url(user, repo, subdir):
    if subdir:
        subdir += '/'
    else:
        subdir = ""
    return 'https://api.github.com/repos/%s/%s/contents/.io.livecode.ch/_site/%sindex.html' % (user, repo, subdir)

def github_content(r):
    return base64.b64decode(r.json()['content']).decode('utf-8')

def github_site_index_src_link(user, repo):
    return 'https://github.com/%s/%s/tree/master/.io.livecode.ch/_site/index.html' % (user, repo)

class UserError(Exception):
    def __init__(self, user, repo, template_file='error_livecode_config.html', status_code=500, ctx=None, err=None, subdir=None):
        self.user = user
        self.repo = repo
        self.template_file = template_file
        self.status_code = status_code
        self.ctx = ctx
        self.err = err
        self.subdir = subdir

@app.errorhandler(UserError)
def handle_user_error(e):
    return render_template(e.template_file, user=e.user, repo=e.repo, status=e.status_code, ctx=e.ctx, err=e.err, subdir=e.subdir), e.status_code

def fetch_defaults(user, repo):
    r_defaults = requests.get(github_defaults_url(user, repo), headers=github_headers)
    if r_defaults.status_code != 200:
        r_check = requests.get(github_check_url(user, repo))
        if r_check.status_code != 200:
            raise UserError(user, repo, 'error_repo_not_found.html', r_check.status_code)
        else:
            raise UserError(user, repo, 'error_livecode_not_found.html', r_defaults.status_code)
    try:
        j_defaults = json.loads(github_content(r_defaults))
    except ValueError as e:
        raise UserError(user, repo, ctx='while parsing <code>defaults.json</code>', err=str(e))
    suffix = request.args.get('img', "")
    o = dkr_check_img(github_dkr_img(user, repo, suffix), github_git_url(user, repo), refresh=request.args.get('refresh', False), suffix=suffix, clone_recursive=j_defaults.get('clone_recursive', True))
    if o['status']!=0:
        raise UserError(user, repo, ctx='while installing', err=o['out'])
    return j_defaults

@app.route("/repl/<user>/<repo>")
@app.route("/repl/<user>/<repo>/<path:content_url>")
def www_github_repl(user, repo, content_url=''):
    j_defaults = fetch_defaults(user, repo)
    content = ''
    if content_url:
        r_content = requests.get('http://'+content_url)
        if r_content.status_code == 200:
            content = r_content.text
    return render_template('repl.html', user=user, repo=repo, content=content, language=j_defaults.get('language'))

@app.route("/learn/<user>/<repo>")
@app.route('/learn/<user>/<repo>/<subdir>')
def www_github_learn(user, repo, subdir=None):
    j_defaults = fetch_defaults(user, repo)
    r_index = requests.get(github_site_index_url(user, repo, subdir), headers=github_headers)
    if r_index.status_code != 200:
        raise UserError(user, repo, 'error_site_not_found.html', r_index.status_code, subdir=subdir)
    try:
        return render_template_string(github_content(r_index), user=user, repo=repo, language=j_defaults.get('language'))
    except TemplateSyntaxError as e:
        raise UserError(user, repo, ctx='while rendering <a href="%s">the site index</a>' % github_site_index_src_link(user, repo), err=str(e))

@app.route("/api/run/<user>/<repo>", methods=['POST'])
def github_run(user, repo):
    suffix = request.args.get('img', "")
    img = github_dkr_img(user, repo, suffix)
    o = dkr_check_img(img, github_git_url(user, repo), suffix=suffix, user=user, repo=repo)
    if o['status']!=0:
        return 'installation error\n%s' % o['out'], 500
    input_main = request.form['main']
    input_pre = request.form['pre']
    input_post = request.form['post']
    key_main = snippet_cache(input_main)
    key_pre = snippet_cache(input_pre)
    key_post = snippet_cache(input_post)
    cache = redis.hget(img, '%s/%s/%s' % (key_main, key_pre, key_post))
    if cache:
        return cache
    o_run = dkr_run(img, 'livecode-run %s %s %s' % (key_main, key_pre, key_post))
    out = o_run['out']
    if o_run['status']!=137 and o_run['status']!=1:
        j_defaults = fetch_defaults(user, repo)
        if j_defaults.get('cache', 'yes')!='no':
            redis.hset(img, '%s/%s/%s' % (key_main, key_pre, key_post), out)
    return out

@app.route("/api/save/<user>/<repo>", methods=['POST'])
def gist_save(user, repo):
    fs = {}
    # Github API does not support empty content
    # so we collect them separately...
    es = []
    for k,v in request.form.items():
        if v.strip()=="":
          es.append(k)
        else:
          fs[k] = {'content': v}
    ev = ",".join(es)
    if ev!="":
      fs['empty.txt'] = {'content':ev}
    data = {}
    data['files'] = fs
    data['description'] = 'io.livecode.ch/learn/%s/%s' % (user, repo)
    data['public'] = True
    gist_create_url = 'https://api.github.com/gists'
    r = requests.post(gist_create_url, json=data, headers=github_headers)
    result = r.json()
    return result.get('id', '')

@app.route("/api/load/<user>/<repo>/<id>")
def gist_load(user, repo, id):
    gist_get_url = 'https://api.github.com/gists/%s' % id
    r = requests.get(gist_get_url, headers=github_headers)
    result = r.json()
    fs = result.get('files', {})
    data = {}
    for k,v in fs.items():
        if k=='empty.txt':
            ev = v['content']
            es = ev.split(',')
            for e in es:
                data[e] = ''
        else:
            data[k] = v['content']
    return jsonify(data)

def snippet_cache(txt):
    key = hashlib.md5(txt.encode('utf-8')).hexdigest()
    fn = os.path.join(SNIPPET_TMP_DIR, key)
    if not os.path.isfile(fn):
        with open(fn, 'w') as f:
            f.write(txt)
    return key

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/howto')
def howto():
    return render_template('howto.html')

@app.errorhandler(404)
def handle_page_not_found(e):
    return render_template('error_404.html', status=e), 404

if __name__ == "__main__":
    if DEBUG:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', threaded=True)
