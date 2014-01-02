from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
from flask import json

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

@app.route("/repl/<user>/<repo>")
def www_github_repl(user, repo):
    r_check = requests.head(github_check_url(user, repo))
    if r_check.status_code == 404:
        return render_template('error_repo_not_found.html', status=r_check.status_code, user=user, repo=repo), r_check.status_code
    r_defaults = requests.get(github_defaults_url(user, repo))
    if r_defaults.status_code == 404:
        return render_template('error_livecode_not_found.html', status=r_defaults.status_code, user=user, repo=repo), r_defaults.status_code
    try:
        j_defaults = r_defaults.json()
    except ValueError as e:
        return render_template('error_livecode_config.html', user=user, repo=repo, status=500, ctx='while parsing <code>defaults.json</code>', err=str(e)), 500
    o = dkr_check_img(github_dkr_img(user, repo), github_git_url(user, repo), refresh=request.args.get('refresh', False))
    if o['status']!=0:
        return render_template('error_livecode_config.html', user=user, repo=repo, status=500, ctx='while installing', err=o.out), 500
    return render_template('repl.html', user=user, repo=repo, language= j_defaults.get('language'))

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
    return o_run['out']

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
def page_not_found(e):
    return render_template('error_404.html', status=e), 404

if __name__ == "__main__":
    app.run()
