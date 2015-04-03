# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging
from flask import redirect, abort, url_for
from flask.ext.mako import MakoTemplates, render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    group_by_start_end,
    parse_xml
)

mako = MakoTemplates(app)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday')


@app.route('/<template>')
def viewer(template):
    """
    Redirects to template.
    """
    sites = {
        'mean_time_weekday': 'Presence mean time',
        'presence_weekday': 'Presence by weekday',
        'presence_start_end': 'Presence start-end',
    }

    try:
        return render_template(template+'.html', selected=template, base=sites)
    except TopLevelLookupException:
        abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def users_view2():
    """
    Users listing for dropdown.
    """
    data = parse_xml()
    return [
        {'user_id': i, 'name': data[i]['name'], 'avatar': data[i]['avatar']}
        for i in data.keys()
    ]


@app.route('/api/v2/presence/<int:user_id>', methods=['GET'])
@jsonify
def user_avatar(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = parse_xml()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    return data[user_id]['avatar']


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/mean_time_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns total time of given user grouped by start end.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_start_end(data[user_id])

    result = [
        (
            calendar.day_abbr[key],
            mean(weekdays[key][0]),
            mean(weekdays[key][1])
        )
        for key in weekdays
    ]

    return result
