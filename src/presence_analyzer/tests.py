# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest
import lxml

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)

# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """
    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_api_users_2(self):
        """
        Test api for data from xml file
        """
        resp = self.client.get('/api/v2/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(
            data[0],
            {
                u'user_id': 176,
                u'name': u'Adrian K.',
                u'avatar': u'https://intranet.stxnext.pl:443/api/images/users/176'
            }
        )

    def test_api_avatar(self):
        """
        Test api for url to user's avatar
        """
        resp = self.client.get('/api/v2/presence/176')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(
            json.loads(resp.data),
            u'https://intranet.stxnext.pl:443/api/images/users/176'
        )

        resp = self.client.get('/api/v2/presence/200')
        self.assertEqual(resp.status_code, 404)

    def test_time_weekday(self):
        resp = self.client.get('/api/v1/mean_time_weekday/12')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/mean_time_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(
            json.loads(resp.data),
            [
                [u'Mon', 24123.0],
                [u'Tue', 16564.0],
                [u'Wed', 25321.0],
                [u'Thu', 22984.0],
                [u'Fri', 6426.0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_presence_weekday_view(self):
        resp = self.client.get('/api/v1/presence_weekday/12')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(
            json.loads(resp.data),
            [
                ["Weekday", "Presence (s)"],
                [u'Mon', 0],
                [u'Tue', 30047],
                [u'Wed', 24465],
                [u'Thu', 23705],
                [u'Fri', 0],
                [u'Sat', 0],
                [u'Sun', 0]
            ]
        )

    def test_presence_start_end_view(self):
        resp = self.client.get('/api/v1/mean_time_start_end/12')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/api/v1/mean_time_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(
            json.loads(resp.data),
            [
                [u'Mon', 0, 0],
                [u'Tue', 34745.0, 64792.0],
                [u'Wed', 33592.0, 58057.0],
                [u'Thu', 38926.0, 62631.0],
                [u'Fri', 0, 0],
                [u'Sat', 0, 0],
                [u'Sun', 0, 0]
            ]
        )

    def test_viewer(self):
        """
        Test viewer templates.
        """
        resp = self.client.get('/mean_time_weekday')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/presence_weekday')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/presence_start_end')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/newsie')
        self.assertEqual(resp.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_parse_xml(self):
        """
        Test parsing of XML file.
        """
        data = utils.parse_xml()
        self.assertItemsEqual(data.keys(), [176, 141])
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data[141].keys(), ['name', 'avatar'])
        self.assertEqual(data[176]['name'], 'Adrian K.')

    def test_group_by_weekday(self):
        data = utils.get_data()
        weekdays = utils.group_by_weekday(data[10])
        self.assertEqual(len(weekdays), 7)
        self.assertEqual(
            weekdays,
            [
                [],
                [30047],
                [24465],
                [23705],
                [],
                [],
                [],
            ]
        )

    def test_seconds_since_midnight(self):
        data = utils.get_data()
        sample_date = datetime.date(2013, 9, 10)
        get_time = data[10][sample_date]['start']

        self.assertEqual(
            utils.seconds_since_midnight(get_time), 34745
        )

        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(1, 0, 0)), 3600
        )

        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(0, 0, 0)), 0
        )

        self.assertEqual(
            utils.seconds_since_midnight(datetime.time(23, 59, 59)), 86399
        )

    def test_interval(self):
        data = utils.get_data()
        sample_date = datetime.date(2013, 9, 10)
        get_time_start = data[10][sample_date]['start']
        get_time_end = data[10][sample_date]['end']
        self.assertEqual(
            utils.interval(get_time_start, get_time_end), 30047
        )

        self.assertEqual(
            utils.interval(datetime.time(1, 1, 1), datetime.time(1, 1, 1)),
            0
        )

        self.assertEqual(
            utils.interval(datetime.time(1, 2, 4), datetime.time(11, 10, 1)),
            36477
        )

        self.assertEqual(
            utils.interval(datetime.time(1, 1, 1), datetime.time(0, 0, 0)),
            -3661
        )

    def test_mean(self):
        self.assertAlmostEqual(utils.mean([2.4, 23.4, 4.3, 45]), 18.775)
        self.assertAlmostEqual(utils.mean([14.1, 26, 35.1, 0.1]), 18.825)
        self.assertAlmostEqual(utils.mean([1, 2, 3, 4]), 2.5)
        self.assertEqual(utils.mean([]), 0)
        self.assertEqual(utils.mean([-1]), -1)
        self.assertEqual(utils.mean([0]), 0)

    def test_group_by_start_end(self):
        data = utils.get_data()
        start_end = utils.group_by_start_end(data[11])
        self.assertEqual(
            start_end,
            {
                0: [[33134], [57257]],
                1: [[33590], [50154]],
                2: [[33206], [58527]],
                3: [[37116, 34088], [60085, 57087]],
                4: [[47816], [54242]],
                5: [[], []],
                6: [[], []],
            }
        )


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
