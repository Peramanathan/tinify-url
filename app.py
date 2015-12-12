#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
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
FECTH_ASSIGNED_VAL = "SELECT v FROM wordlist WHERE k= ?"
FETCH_ALL_UNASSIGNED_KEYS = "SELECT k FROM wordlist WHERE v='not assigned'"
ROWS_UNASSIGNED = "SELECT count(*) FROM wordlist WHERE v='not assigned'"
UPDATE_KEY_VALS = "INSERT OR REPLACE INTO wordlist (k, v) VALUES (?,?)"

# Semantic variables
FIRST_ROW = FIRST_COL = 0

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def update_db(query, args=()):
    app.logger.info("updating db: KEY/VALS: " + str(args))
    db = get_db()
    db.execute(query, args)
    db.commit()


def is_key_assigned(word):

    cur = query_db(FECTH_ASSIGNED_VAL, [word])

    try:
        assigned_value = cur[0][0] if cur else None
        if assigned_value == 'not assigned':
            return False
        elif assigned_value is None:
            return True
        elif len(assigned_value) > 0:  # key is assigned already
            return True
    except Exception, e:
        app.logger.error(e)

    return False


def has_prefix_keyword(prefix):
    app.logger.info(prefix)
    if len(prefix) == 0:
        return None
    elif not is_key_assigned(prefix):
        return prefix
    else:
        has_prefix_keyword(prefix[:-1])


def has_suffix_keyword(suffix):
    app.logger.info(suffix)
    if len(suffix) == 0:
        return None
    elif not is_key_assigned(suffix):
        return suffix
    else:
        has_suffix_keyword(suffix[1:])


def find_and_update_keyword(keywords, long_url):

    # High probability for url to contain  english words
    for keyword in keywords:
        app.logger.info(keyword)
        if not is_key_assigned(keyword):
            update_db(UPDATE_KEY_VALS, [keyword, long_url])
            return keyword

        prefix = keyword[:-1]
        prefix_keyword = has_prefix_keyword(prefix)
        app.logger.info(prefix_keyword)
        if prefix_keyword:
            update_db(UPDATE_KEY_VALS, [prefix_keyword, long_url])
            return prefix_keyword

        suffix = keyword[1:]
        suffix_keyword = has_suffix_keyword(suffix)
        if suffix_keyword:
            update_db(UPDATE_KEY_VALS, [suffix_keyword, long_url])
            return suffix_keyword

    try:
        # Checking if all keys are assigned
        cur = query_db(ROWS_UNASSIGNED)
        nr_rows = cur[FIRST_ROW][FIRST_COL] if cur else 0
        app.logger.info(nr_rows)
        if not nr_rows:
            pass  # have to reassign the oldest key

        random_index = randint(1, nr_rows)
        keyword_cur = query_db(FETCH_ALL_UNASSIGNED_KEYS)
        random_keyword = keyword_cur[random_index][0]
        update_db(UPDATE_KEY_VALS, [random_keyword, long_url])

        return random_keyword
    except Exception, e:
        app.logger.error(e)

    return None  # pick oldest assigned key


def regex_url_cleaner(url_string):
    # words = re.split('/|\-|\?|\=|\_|\&|\+|\%| ', url_string)
    words = re.split('\W+|\_', url_string)  # As unicode set it ignore _
    words = map(lambda x: x.lower(), words)
    return filter(None, words)


def tinify_url(long_url):
    keywords = []
    parsed_url = urlparse(long_url.strip())
    for ustr in parsed_url:
        keywords += regex_url_cleaner(ustr)
    app.logger.info(keywords)
    keyword = find_and_update_keyword(sorted(keywords), long_url)
    app.logger.info(keyword)

    return "http://myurlshortner.com/" + keyword


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
    cur = query_db(FECTH_ASSIGNED_VAL, [word])
    external_url = cur[FIRST_ROW][FIRST_COL] if cur else None
    app.logger.info(external_url)
    if external_url is None or external_url == 'not assigned':
        external_url = "http://fyndiq.se"

    return redirect(external_url, code=302)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
