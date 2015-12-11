#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import marisa_trie
import sqlite3
from datetime import datetime
from random import seed, choice, uniform, randint, sample
from urlparse import urlparse
from flask import Flask, g, render_template, redirect, url_for, \
    request, jsonify, abort
from contextlib import closing

NOW = datetime.now()
SEED_VAL = sum([val for val in NOW.timetuple()])
seed(SEED_VAL)

# Configuration
DATABASE = 'wordlist.db'
DEBUG = True
SECRET_KEY = os.urandom(24)

# Queries
FECTH_ASSIGNED_VAL_QUERY = "select v from wordlist where k= ?"
FETCH_ALL_UNASSIGNED_KEYS = "select k from wordlist where v='not assigned'"

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def is_contain(word):

    # query = "select v from wordlist where k= '" + word + "';"
    # query = "select v from wordlist where k= ?"
    cur = query_db(FECTH_ASSIGNED_VAL_QUERY, [word])

    try:
        assigned_value = cur[0][0] if cur else None
        if assigned_value == 'not assigned':
            return True
        elif assigned_value is None:
            return False
        elif len(assigned_value) > 0:  # key is assigned already
            return False
    except Exception, e:
        app.logger.error(e)

    return False


def find_keyword(keywords):

    for keyword in keywords:
        app.logger.info(keyword)
        if is_contain(keyword):
            return keyword

    try:
        # Checking if all keys are assigned
        cur = query_db(FETCH_ALL_UNASSIGNED_KEYS)
        random_keyword = cur[0][0]
        return random_keyword
    except Exception, e:
        app.logger.error(e)

    return None  # pick oldest assigned key


def tinify_url(long_url):
    keywords = []
    parsed_url = urlparse(long_url.strip())
    keywords_in_domain = parsed_url.netloc.split('.')  # netloc: techcrunch.com
    keywords_in_path = re.split('/|\-', parsed_url.path)  # path:/lawsuit/
    keywords = keywords_in_domain + keywords_in_path
    keywords = filter(None, keywords)

    keyword = find_keyword(sorted(keywords))

    return "http://myurlshortner.com/" + keyword


@app.before_request
def before_request():
    g.db = get_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route("/", methods=['GET', 'POST'])
def index():
    urls = None
    if request.method == 'POST':
        full_url = request.form['longUrl']
        tinified_url = tinify_url(full_url)
        urls = {"tiny_url": tinified_url, "long_url": full_url}
    return render_template('index.html', urls=urls)


@app.route("/<word>", methods=['GET'])
def redirect_to_external(word):
    external_url = query_db(FECTH_ASSIGNED_VAL_QUERY, [word])
    app.logger.info(external_url)
    if external_url != 'not assigned' or external_url is None:
        external_url = "http:google.com"
    return redirect(external_url)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
