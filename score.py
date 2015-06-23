#!/usr/bin/env python
#
# Copyright (C) 2015 Red Hat, Inc.
#
# Author: Frederic Lepied <frederic.lepied@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

'''
'''

from __future__ import print_function
import glob
import json
import os
import re
import sys


def html(out, *items):
    for item in items:
        out.write(item + '<br/>\n')


def score_review(review_json_str, patch, exceptions,
                 review_url="https://review.openstack.org/#/q/%s,n,z"):
    data = json.loads(review_json_str)
    score = []
    if 'type' in data and data['type'] == 'stats' \
       or data['status'] == 'NONE':
        for exception in exceptions:
            if re.search(exception, patch):
                return ((50,
                         '<a href="%s/patch">Patch</a>'
                        ' is downstream only -> +50'
                         % patch),)
        else:
            return ((200, '<a href="%s/patch">Patch</a> '
                     'not submitted upstream -> +200'
                     % patch),)
    elif data['status'] == 'NEW':
        score.append(
            (20, ('<a href="%s/patch">Patch</a> not merged upstream -> +20 '
                  '(<a href="%s">review</a>)'
                  % (patch, review_url % data['id']))))
    elif data['status'] == 'MERGED':
        return ((10, '<a href="%s/patch">Patch</a> merged upstream -> +10 '
                 '(<a href="%s">review</a>)'
                 % (patch, review_url % data['id'])),)
    elif data['status'] == 'ABANDONED':
        return ((150, '<a href="%s/patch">Patch</a> '
                 'abandoned upstream -> +150 '
                 '(<a href="%s">review</a>)'
                 % (patch, review_url % data['id'])),)
    elif data['status'] == 'CHERRY':
        return ((10, '<a href="%s/patch">Patch</a> '
                 'cherry-picked upstream -> +10' %
                 patch),)
    else:
        return ((200, '<a href="%s/patch">Patch</a> '
                 'has unknown status: %s -> +200'
                 % (patch, data['status'])),)
    lowest = 3
    for approval in data['patchSets'][-1]['approvals']:
        if (approval['type'] == 'Verified' and
           approval['by']['username'] == 'jenkins'):
            if approval['value'] == '-1':
                score.append((50, 'Do not pass Jenkins -> +50'))
        elif approval['type'] == 'Code-Review':
            if lowest > int(approval['value']):
                lowest = int(approval['value'])
            if approval['value'] == '+2':
                score.append((-10, 'Got a +2 -> -10'))
    if lowest == -2:
        score.append((100, 'Lowest vote is -2 -> +100'))
    elif lowest == -1:
        score.append((50, 'Lowest vote is -1 -> +50'))
    elif lowest == 1:
        score.append((-5, 'Lowest vote is +1 -> -5'))
    return score


def score_interdiff(interdiff_lines, patch):
    changes = 0
    for line in interdiff_lines[1:]:
        elts = line.split(',')
        changes += int(elts[0]) + int(elts[1]) + int(elts[2])
    if changes == 0:
        return (0, 'Difference to upstream patchset is null -> 0 '
                '(<a href="%s/interdiff.patch">interdiff</a>)' % patch)
    elif changes <= 25:
        return (10, 'Difference to upstream patchset is small -> +10 '
                '(<a href="%s/interdiff.patch">interdiff</a>)' % patch)
    else:
        return (100, 'Difference to upstream patchset is big -> +100 '
                '(<a href="%s/interdiff.patch">interdiff</a>)' % patch)


def main():
    global_score = 0

    exceptions = {
        'python-django-horizon': ['Change-branding.patch'],
    }

    target_name = os.path.basename(sys.argv[1])
    out = open(os.path.join(sys.argv[1], 'score.html'), 'w')

    for package_name in exceptions:
        if target_name[:len(package_name)] == package_name:
            exception = exceptions[package_name]
            break
    else:
        exception = ()

    for path in sorted(glob.glob(os.path.join(sys.argv[1], '*.patch'))):
        patch = os.path.basename(path)
        out.write('<h3><a href=\"%s\">%s</a></h3>\n' % (patch, patch))
        scores = score_review(
            open(os.path.join(path, 'review.json')).readline(),
            patch, exception)
        for score, reason in scores:
            html(out, reason)
            global_score += score
        html(out, '')
        score, reason = score_interdiff(
            open(
                os.path.join(
                    path, 'interdiff.diffstat')).readlines(), patch)
        global_score += score
        html(out, reason)
        html(out, '')

    html(out, '<hr/>Global score %d' % global_score)
    print(global_score)

    out.close()

if __name__ == "__main__":
    main()

# score.py ends here
