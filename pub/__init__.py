from flask import Flask
from flask import request
from flask import render_template
from flask import render_template_string
from flask import jsonify
from flask import json
from jinja2.exceptions import TemplateSyntaxError

import os

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')
if 'DOCKER_HOST' not in app.config:
    app.config['DOCKER_HOST'] = os.environ.get('DOCKER_HOST', 'unix://var/run/docker.sock')
if not os.path.exists(app.config['SNIPPET_TMP_DIR']):
    os.makedirs(app.config['SNIPPET_TMP_DIR'])

from redis import Redis
redis = Redis()

import docker

import hashlib
import re

import requests

def dkr_base_img():
    return app.config['DKR_BASE_IMAGE']

def dkr_client():
    return docker.Client(base_url=app.config['DOCKER_HOST'],
                         version='1.13',
                         timeout=10)

def dkr_check_img(img, git_url, refresh=False):
    c = dkr_client()
    if refresh:
        redis.delete(img)
    if not refresh and c.images(img) != []:
        return {'status':0, 'out':'already installed'}
    m = c.create_container(dkr_base_img(), 'git clone "%s" /home/runner/code' % git_url, user='runner')
    id = m['Id']
    c.start(id)
    s = c.wait(id)
    if s!=0:
        return {'status':s, 'out':'error cloning repository %s' % git_url}
    c.commit(id, img)
    return dkr_run(img, 'livecode-install', img, c=c)

def dkr_run(img, cmd, commit=None, timeout=5, c=None):
    c = c or dkr_client()
    r = ""
    m = c.create_container(img,
                           "timeout %d %s" % (timeout, cmd),
                           user='runner',
                           environment={'HOME':'/home/runner'},
                           volumes=['/mnt/snippets'],
                           network_disabled=True)
    id = m['Id']
    c.start(id, binds={app.config['SNIPPET_TMP_DIR']: { 'bind': '/mnt/snippets', 'ro': True }})
    s = c.wait(id)
    if s!=0:
        r += "error: (%d)\n" % s
    if s==137:
        r += "killed!"
    elif s==125:
        r += "timeout!"
    elif s==124:
        r += "inifinite loop!"
    else:
        r += c.logs(id)
    if commit:
        c.commit(id, repository=commit)
    return {'status':s, 'out':r}

def github_dkr_img(user, repo):
    return '%s/github.com/%s/%s' % (app.config['DKR_IMAGE_PREFIX'], user, repo)

def github_check_url(user, repo):
    return 'https://github.com/%s/%s' % (user, repo)

def github_git_url(user, repo):
    return 'https://github.com/%s/%s.git' % (user, repo)

def github_defaults_url(user, repo):
    return 'https://raw.github.com/%s/%s/master/.io.livecode.ch/defaults.json' % (user, repo)

def github_site_index_url(user, repo, subdir):
    if subdir:
        subdir += '/'
    else:
        subdir = ""
    return 'https://raw.github.com/%s/%s/master/.io.livecode.ch/_site/%sindex.html' % (user, repo, subdir)

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
    r_defaults = requests.get(github_defaults_url(user, repo))
    if r_defaults.status_code != 200:
        r_check = requests.get(github_check_url(user, repo))
        if r_check.status_code != 200:
            raise UserError(user, repo, 'error_repo_not_found.html', r_check.status_code)
        else:
            raise UserError(user, repo, 'error_livecode_not_found.html', r_defaults.status_code)
    try:
        j_defaults = r_defaults.json()
    except ValueError as e:
        raise UserError(user, repo, ctx='while parsing <code>defaults.json</code>', err=str(e))
    o = dkr_check_img(github_dkr_img(user, repo), github_git_url(user, repo), refresh=request.args.get('refresh', False))
    if o['status']!=0:
        raise UserError(user, repo, ctx='while installing', err=o['out'])
    return j_defaults

@app.route("/repl/<user>/<repo>")
@app.route("/repl/<user>/<repo>/<path:content_url>")
def www_github_repl(user, repo, content_url):
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
    r_index = requests.get(github_site_index_url(user, repo, subdir))
    if r_index.status_code != 200:
        raise UserError(user, repo, 'error_site_not_found.html', r_index.status_code, subdir=subdir)
    try:
        return render_template_string(r_index.text, user=user, repo=repo, language=j_defaults.get('language'))
    except TemplateSyntaxError as e:
        raise UserError(user, repo, ctx='while rendering <a href="%s">the site index</a>' % github_site_index_src_link(user, repo), err=str(e))

@app.route("/api/run/<user>/<repo>", methods=['POST'])
def github_run(user, repo):
    o = dkr_check_img(github_dkr_img(user, repo), github_git_url(user, repo))
    if o['status']!=0:
        return 'installation error\n%s' % o.out, 500
    input_main = request.form['main']
    input_pre = request.form['pre']
    input_post = request.form['post']
    key_main = snippet_cache(input_main)
    key_pre = snippet_cache(input_pre)
    key_post = snippet_cache(input_post)
    cache = redis.hget(github_dkr_img(user, repo), '%s/%s/%s' % (key_main, key_pre, key_post))
    if cache:
        return cache
    o_run = dkr_run(github_dkr_img(user, repo), 'livecode-run %s %s %s' % (key_main, key_pre, key_post))
    out = o_run['out']
    if o_run['status']!=137:
        redis.hset(github_dkr_img(user, repo), '%s/%s/%s' % (key_main, key_pre, key_post), out)
    return out

def snippet_cache(txt):
    key = hashlib.md5(txt.encode('utf-8')).hexdigest()
    fn = os.path.join(app.config['SNIPPET_TMP_DIR'], key)
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
    app.run(host='0.0.0.0', threaded=True)
