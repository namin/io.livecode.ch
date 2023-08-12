from flask import Flask
from flask import request
from flask import render_template
from flask import jsonify
import os
import json
import requests

app = Flask(__name__)

def proxy_github_post(action, user, repo):
    data = {}
    for k,v in request.values.items():
        data[k] = v
    r = requests.post('https://%s/api/%s/%s/%s' % (os.environ.get('REMOTE_SERVER_NAME', 'io.livecode.ch'), action, user, repo), data)
    return r.text, r.status_code

@app.route("/api/run", methods=['GET','POST'])
def proxy_github_run0():
    user = request.values['user']
    repo = request.values['repo']
    return proxy_github_post('run', user, repo)

@app.route("/api/run/<user>/<repo>", methods=['GET','POST'])
def proxy_github_run(user, repo):
    return proxy_github_post('run', user, repo)

@app.route("/api/save/<user>/<repo>", methods=['GET','POST'])
def proxy_github_save(user, repo):
    return proxy_github_post('save', user, repo)

@app.route("/api/load/<user>/<repo>/<id>")
def proxy_gist_load(user, repo, id):
    r = requests.get('http://%s/api/load/%s/%s/%s' % (os.environ.get('REMOTE_SERVER_NAME', 'io.livecode.ch'), user, repo, id))
    result = r.json()
    return jsonify(result)

@app.route('/')
def local_index():
    return render_template("local/index.html")

def local_defaults(user, repo):
    with open('templates/local/%s/.io.livecode.ch/defaults.json' % repo) as f_defaults:
        return json.load(f_defaults)

@app.route('/learn/<user>/<repo>')
@app.route('/learn/<user>/<repo>/<subdir>')
def local_preview(user, repo, subdir=None):
    j_defaults = local_defaults(user, repo)
    if subdir:
        subdir += '/'
    else:
        subdir = ""
    return render_template('local/%s/.io.livecode.ch/_site/%sindex.html' % (repo, subdir), user=user, repo=repo, language=j_defaults.get('language'))

@app.route('/debug/<path:p>')
def debug_page(p):
    return render_template(p+'.html')

if __name__ == "__main__":
    app.run(debug=True)
