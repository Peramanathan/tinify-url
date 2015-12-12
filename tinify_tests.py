import os
import tinify
import unittest
import tempfile
from datetime import datetime


class TinifyTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, tinify.app.config['DATABASE'] = tempfile.mkstemp()
        tinify.app.config['TESTING'] = True
        self.app = tinify.app.test_client()
        with tinify.app.app_context():
            tinify.init_db()
            tinify.update_db(tinify.ASSIGN_KEYVALS_QUERY,
                             ['mail', 'not assigned', datetime.now()])
            tinify.update_db(tinify.ASSIGN_KEYVALS_QUERY,
                             ['need', 'not assigned', datetime.now()])
            tinify.update_db(tinify.ASSIGN_KEYVALS_QUERY,
                             ['we', 'not assigned', datetime.now()])
            tinify.update_db(tinify.ASSIGN_KEYVALS_QUERY,
                             ['test', 'http:testing.com', datetime.now()])

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(tinify.app.config['DATABASE'])

    def feed_sample_url(self):
        long_url = "techcrunch.com/2015/11/10/gmail-we-need-to-talk"
        return self.app.post('/', data=dict(longUrl=long_url),
                             follow_redirects=True)

    def get_key_for_url(self, long_url):
        return self.app.post('/', data=dict(longUrl=long_url),
                             follow_redirects=True)

    def goto_path(self, word):
        return self.app.get('/' + word)

    # Unit & Integration test 1: is index correctly loaded? code 200
    def test_index(self):
        rv = self.app.get('/')
        assert 'paste your long url' in rv.data

    # Unit & Integration test 2: does long url feed result in short url?
    def test_feed_url(self):
        rv = self.feed_sample_url()
        href = "techcrunch.com/2015/11/10/gmail-we-need-to-talk"
        shorturl = "http://myurlshortner.com/mail"
        assert href in rv.data
        assert shorturl in rv.data

    # Unit & Integration test 3: redirection works?
    def test_redirection(self):
        rv = self.goto_path('test')
        info = 'You should be redirected automatically to target URL: '
        redirection_url = '<a href="http:testing.com">http:testing.com</a>'
        success = info + redirection_url
        assert success in rv.data


if __name__ == '__main__':
    unittest.main()
