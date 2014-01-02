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

import requests

def dkr_base_img():
    return 'namin/'+app.config['SERVER_NAME']

def dkr_check_img(img, git_url, refresh=False, timeout=60, cmd=".io.livecode.ch/install"):
    c = docker.Client(base_url='unix://var/run/docker.sock',
                           version='1.8',
                           timeout=10)
    if not refresh and c.images(img) != []:
        return {'status':0, 'out':'already installed'}
    return dkr_run(dkr_base_img(), '/home/runner/bin/livecode-install %d %s %s' % (timeout, cmd, git_url), img)

def dkr_run(img, cmd, commit=None):
    c = docker.Client(base_url='unix://var/run/docker.sock',
                           version='1.8',
                           timeout=10)
    m = c.create_container(img, cmd, user='runner', environment={'HOME':'/home/runner'})
    id = m['Id']
    c.start(id)
    s = c.wait(id)
    r = ""
    if s!=0:
        r += "error: (%d)\n" % s
    if s==125:
        r += "timeout!"
    elif s==124:
        r += "inifinite loop!"
    else:
        r += c.logs(id)
    if commit:
        c.commit(id, repository=commit)
    c.remove_container(id)
    return {'status':s, 'out':r}

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
    r_check = requests.head(github_check_url(user, repo))
    if r_check.status_code != 200:
        raise UserError(user, repo, 'error_repo_not_found.html', r_check.status_code)
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
    o_run = dkr_run(
        github_dkr_img(user, repo),
        '/home/runner/bin/livecode-run %d %s %s %s %s' % (
            10,
            request.form.get('cmd', './.io.livecode.ch/run'),
            url_main, url_pre, url_post))
    out = o_run['out']
    if o_run['status']==0:
        # remove wget noise -- first three lines
        n = 0
        for i in range(0, 3):
            n = out.index('\n', n)+1
        out = out[n:-1]
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
