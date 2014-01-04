from flask import Flask
from flask import request
from flask import render_template
from flask import render_template_string
from flask import jsonify
from flask import json
from jinja2.exceptions import TemplateSyntaxError

app = Flask(__name__)
app.config.from_envvar('APP_SETTINGS')

from redis import Redis
redis = Redis()

import docker

import hashlib
import re

import requests

def dkr_base_img():
    return 'namin/'+app.config['SERVER_NAME']

def dkr_parse_id(txt):
    m = re.search(r'{"id":"([^"]*)"}', txt)
    if m:
        return m.group(1)
    else:
        return None

def dkr_check_img(img, git_url, refresh=False):
    c = docker.Client(base_url='unix://var/run/docker.sock',
                           version='1.8',
                           timeout=10)
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
    try:
        c.commit(id, img)
        return dkr_run(img, 'livecode-install', img, c=c)
    finally:
        c.remove_container(id)

def dkr_run(img, cmd, commit=None, timeout=5, insert_files=None, c=None):
    if not c:
        c = docker.Client(base_url='unix://var/run/docker.sock',
                          version='1.8',
                          timeout=10)
    r = ""
    tmp_imgs = []
    if insert_files:
        for file_name, file_url in insert_files.iteritems():
            txt = c.insert(img, file_url, '/home/runner/files/%s' % file_name)
            tmp_img = dkr_parse_id(txt)
            if tmp_img:
                tmp_imgs.append(tmp_img)
                img = tmp_img
    m = c.create_container(img, "timeout %d %s" % (timeout, cmd), user='runner', environment={'HOME':'/home/runner'}, network_disabled=True)
    id = m['Id']
    c.start(id)
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
    try:
        return {'status':s, 'out':r}
    finally:
        c.remove_container(id)
        if tmp_imgs!=[]:
            for i in tmp_imgs:
                c.remove_container(c.inspect_image(i)['container'])
            c.remove_image(tmp_imgs[-1])

def github_dkr_img(user, repo):
    return 'temp/%s/github.com/%s/%s' % (app.config['SERVER_NAME'], user, repo)

def github_check_url(user, repo):
    return 'https://api.github.com/repos/%s/%s' % (user, repo)

def github_git_url(user, repo):
    return 'https://github.com/%s/%s.git' % (user, repo)

def github_defaults_url(user, repo):
    return 'https://raw.github.com/%s/%s/master/.io.livecode.ch/defaults.json' % (user, repo)

def github_site_index_url(user, repo):
    return 'https://raw.github.com/%s/%s/master/.io.livecode.ch/_site/index.html' % (user, repo)

def github_site_index_src_link(user, repo):
    return 'https://github.com/%s/%s/tree/master/.io.livecode.ch/_site/index.html' % (user, repo)

class UserError(Exception):
    def __init__(self, user, repo, template_file='error_livecode_config.html', status_code=500, ctx=None, err=None):
        self.user = user
        self.repo = repo
        self.template_file = template_file
        self.status_code = status_code
        self.ctx = ctx
        self.err = err

@app.errorhandler(UserError)
def handle_user_error(e):
    return render_template(e.template_file, user=e.user, repo=e.repo, status=e.status_code, ctx=e.ctx, err=e.err), e.status_code

def fetch_defaults(user, repo):
    #r_check = requests.head(github_check_url(user, repo))
    #if r_check.status_code != 200:
    #    raise UserError(user, repo, 'error_repo_not_found.html', r_check.status_code)
    r_defaults = requests.get(github_defaults_url(user, repo))
    if r_defaults.status_code != 200:
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
def www_github_repl(user, repo):
    j_defaults = fetch_defaults(user, repo)
    return render_template('repl.html', user=user, repo=repo, language=j_defaults.get('language'))

@app.route("/learn/<user>/<repo>")
def www_github_learn(user, repo):
    j_defaults = fetch_defaults(user, repo)
    r_index = requests.get(github_site_index_url(user, repo))
    if r_index.status_code != 200:
        raise UserError(user, repo, 'error_site_not_found.html', r_index.status_code)
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
    url_main = snippet_cache(input_main)
    url_pre = snippet_cache(input_pre)
    url_post = snippet_cache(input_post)
    cache = redis.hget(github_dkr_img(user, repo), '%s/%s/%s' % (url_main, url_pre, url_post))
    if cache:
        return cache
    o_run = dkr_run(github_dkr_img(user, repo), 'livecode-run', insert_files={'main.txt':url_main, 'pre.txt':url_pre, 'post.txt':url_post})
    out = o_run['out']
    if o_run['status']!=137:
        redis.hset(github_dkr_img(user, repo), '%s/%s/%s' % (url_main, url_pre, url_post), out)
    return out

@app.route('/api/snippet/<key>')
def snippet(key):
    txt = redis.hget('snippet', key)
    if txt is not None:
        return txt
    else:
        return 'None', 404

def snippet_cache(txt):
    key = hashlib.md5(txt.encode('utf-8')).hexdigest()
    redis.hset('snippet', key, txt)
    return 'http://%s/api/snippet/%s' % (app.config['SERVER_NAME'], key)

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def handle_page_not_found(e):
    return render_template('error_404.html', status=e), 404

if __name__ == "__main__":
    app.run()
