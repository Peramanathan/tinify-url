import os
import tinify
import unittest
import tempfile


class TinifyTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, tinify.app.config['DATABASE'] = tempfile.mkstemp()
        tinify.app.config['TESTING'] = True
        self.app = tinify.app.test_client()
        with tinify.app.app_context():
            tinify.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(tinify.app.config['DATABASE'])

    def feed_url(self):
        long_url = """techcrunch.com/2015/11/10/gmail-we-need-to-talk/
        ?ncid=rss&utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+
        Techcrunch+%28TechCrunch%29&utm_content=FaceBook&sr_share=facebook"""

        return self.app.post('/', data=dict(longUrl=long_url),
                             follow_redirects=True)

    def test_index(self):
        rv = self.app.get('/')
        assert 'paste your long url' in rv.data


if __name__ == '__main__':
    unittest.main()
