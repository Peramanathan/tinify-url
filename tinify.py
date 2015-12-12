#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This small app does find a tinified url for the given long url"""

import os
import re
import sqlite3
from datetime import datetime
from random import seed, randint
from urlparse import urlparse
from flask import Flask, g, render_template, redirect, \
    request

NOW = datetime.now()
SEED_VAL = sum([val for val in NOW.timetuple()])
seed(SEED_VAL)

# Configuration
DATABASE = 'wordlist.db'
DEBUG = True
SECRET_KEY = os.urandom(24)

# Queries
ASSIGNED_VAL_QUERY = "SELECT v FROM wordlist WHERE k= ?"
ALL_UNASSIGNED_KEYS_QUERY = "SELECT k FROM wordlist WHERE v='not assigned'"
ROWS_UNASSIGNED_QUERY = "SELECT count(*) FROM wordlist WHERE v='not assigned'"
ASSIGN_KEYVALS_QUERY = "INSERT OR REPLACE INTO wordlist(k,v,up) VALUES (?,?,?)"
REPLACE_OLDEST_KEY_QUERY = """UPDATE wordlist SET  v=?, up=?
                              WHERE up IN (
                                SELECT up FROM wordlist ORDER BY up ASC LIMIT 1
                              )"""
OLDEST_KEY_QUERY = "SELECT k FROM wordlist ORDER BY up ASC LIMIT 1"

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


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def query_db(query, args=(), one=False):
    """ Select rows for the given query """
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def update_db(query, args=()):
    """ Update the rows for the given query """
    app.logger.info("updating db: KEY/VALS: " + str(args))
    db = get_db()
    db.execute(query, args)
    db.commit()


@app.teardown_appcontext
def close_db(error):
    """Closes the database at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def is_key_assigned(word):
    """For the given word it checks if the word is already assigned a url"""
    cur = query_db(ASSIGNED_VAL_QUERY, [word])
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
    """ Recursively search if any of prefixes of prefix(word) including
        itself is already assigned a url
    """
    if len(prefix) == 0:
        return None
    elif not is_key_assigned(prefix):
        return prefix
    else:
        has_prefix_keyword(prefix[:-1])


def has_suffix_keyword(suffix):
    """ Recursively search if any of suffixes of suffix(word) including
        itself is already assigned a url
    """
    if len(suffix) == 0:
        return None
    elif not is_key_assigned(suffix):
        return suffix
    else:
        has_suffix_keyword(suffix[1:])


def find_and_update_keyword(keywords, long_url):   # O(len(parsed_url))
    """ For the given list of words in the parsed url it will find a keyword
        and update the url against correct keyword in database
    """
    for keyword in keywords:

        if not is_key_assigned(keyword):
            update_db(ASSIGN_KEYVALS_QUERY,
                      [keyword, long_url, datetime.now()])
            return keyword

        prefix = keyword[:-1]
        prefix_keyword = has_prefix_keyword(prefix)
        if prefix_keyword:
            app.logger.info("prefix found: " + prefix_keyword)
            update_db(ASSIGN_KEYVALS_QUERY,
                      [prefix_keyword, long_url, datetime.now()])
            return prefix_keyword

        suffix = keyword[1:]
        suffix_keyword = has_suffix_keyword(suffix)
        if suffix_keyword:
            app.logger.info("suffix found: " + suffix_keyword)
            update_db(ASSIGN_KEYVALS_QUERY,
                      [suffix_keyword, long_url, datetime.now()])
            return suffix_keyword

    try:
        # Checking if all keys are assigned
        cur = query_db(ROWS_UNASSIGNED_QUERY)
        nr_rows = cur[FIRST_ROW][FIRST_COL] if cur else 0
        app.logger.info("# Unassinged keys: " + str(nr_rows))
        if not nr_rows:
            oldest_key_cur = query_db(OLDEST_KEY_QUERY)
            oldest_key = oldest_key_cur[FIRST_ROW][FIRST_COL]
            update_db(REPLACE_OLDEST_KEY_QUERY, long_url, datetime.now())
            return oldest_key

        random_index = randint(0, nr_rows - 1)
        keyword_cur = query_db(ALL_UNASSIGNED_KEYS_QUERY)
        random_keyword = keyword_cur[random_index][0]
        app.logger.info(random_keyword)
        update_db(ASSIGN_KEYVALS_QUERY,
                  [random_keyword, long_url, datetime.now()])

        return random_keyword
    except Exception, e:
        app.logger.error(e)

    return None


def regex_url_cleaner(url_string):
    """ Cleans the url removes non alphanumeric chars and _ and makes all the words
        into lowercase
    """
    words = re.split('\W+|\_', url_string)  # As unicode set it ignore _
    words = map(lambda x: x.lower(), words)
    return filter(None, words)


def tinify_url(long_url):
    """For the given full length url it retruns tinified url for
       following specific scheme
    """
    keywords = []
    parsed_url = urlparse(long_url.strip())
    for ustr in parsed_url:
        keywords += regex_url_cleaner(ustr)
    app.logger.info(sorted(keywords))
    keyword = find_and_update_keyword(sorted(keywords), long_url)

    return "http://myurlshortner.com/" + keyword


@app.route("/", methods=['GET', 'POST'])
def index():
    """Index page"""
    urls = None
    if request.method == 'POST':
        full_url = request.form['longUrl']
        tinified_url = tinify_url(full_url)
        urls = {"tiny_url": tinified_url, "long_url": full_url}
    return render_template('index.html', urls=urls)


@app.route("/<word>", methods=['GET'])
def redirect_to_external(word):
    """Redirction page"""
    cur = query_db(ASSIGNED_VAL_QUERY, [word])
    external_url = cur[FIRST_ROW][FIRST_COL] if cur else None
    app.logger.info(external_url)
    if external_url is None or external_url == 'not assigned':
        external_url = "http://fyndiq.se"

    return redirect(external_url, code=302)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
