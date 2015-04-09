# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
from __future__ import unicode_literals

import csv
import time
import threading
from json import dumps
from functools import wraps
from datetime import datetime
from lxml import etree

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

CACHE = {}


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def locker(function):
    """
    Starting new thread.
    """
    @wraps(function)
    def _locker(*args, **kwrgs):
        """
        Locking function.
        """
        run_thread = threading.Thread(target=function, args=args)
        run_thread.start()
        return function(*args, **kwrgs)
    return _locker


def is_obsolete(entry, duration):
    """
    Checking if cache time is older than duration.
    """
    return time.time() - entry['time'] > duration


def memoize(duration):
    """
    Creating cache with users' data.
    """
    def _memoize(function):
        """
        Taking a function.
        """
        def __memoize(*args, **kw):
            """
            Creating cache.
            """
            key = "user_data"
            if key in CACHE and not is_obsolete(CACHE[key], duration):
                return CACHE[key]['value']
            result = function(*args, **kw)
            CACHE[key] = {'value': result, 'time': time.time()}
            return result
        return __memoize
    return _memoize


@locker
@memoize(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=str(','))
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def parse_xml():
    """
    Extracts users' name and avatar from given xml document.
    """
    data = {}
    tree = etree.parse(app.config['DATA_XML'])
    root = tree.getroot()
    serv = ('{}://{}:{}'.format(
        root.findtext('./server/protocol'),
        root.findtext('./server/host'),
        root.findtext('./server/port')
        ))

    for user in root.findall('./users/user'):
        avatar = ''.join((serv, user.find('avatar').text))
        name = user.find('name').text
        data[int(user.get('id'))] = {'name': name, 'avatar': avatar}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def group_by_start_end(items):
    """
    Calculates mean time start and end.
    """
    result = {key: [[], []] for key in range(7)}

    for date in items:
        result[date.weekday()][0].append(
            seconds_since_midnight(items[date]['start'])
        )
        result[date.weekday()][1].append(
            seconds_since_midnight(items[date]['end']))

    return result
