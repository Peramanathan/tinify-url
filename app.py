#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from urlparse import urlparse
import sqlite3
from flask import Flask, render_template, redirect, url_for, \
    request, jsonify, abort
from contextlib import closing

# configuration
DATABASE = 'wordlist.db'
DEBUG = True
SECRET_KEY = os.urandom(24)

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def tinify_url(long_url):
    keywords = []
    parsed_url = urlparse(long_url.strip())
    keywords_in_domain = parsed_url.netloc.split('.')  # netloc: techcrunch.com
    keywords_in_path = re.split('/|\-', parsed_url.path)  # path: /././pinterest-­lawsuit/
    keywords = keywords_in_domain + keywords_in_path
    keywords = filter(None, keywords)
    query = "select v from wordlist where k= '" + "law" + "';"

    db = connect_db()
    app.logger.info(db.execute(query).fetchall())
    app.logger.info(keywords)
    return "http://myurlshortner.com/" + sorted(keywords)[0]


@app.route("/", methods=['GET', 'POST'])
def index():
    tinified_url = None
    if request.method == 'POST':
        tinified_url = tinify_url(request.form['longUrl'])
    return render_template('index.html', tiny_url=tinified_url)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
