#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from optparse import OptionParser, Option

from builders.util import shell_call, color_print

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

usage = "usage: %prog -h"

option_list = (
    Option(
        '--plus',
        action='store_true',
        dest='plus',
        help='Run with nginx+ (false by default)',
        default=False,
    ),
    Option(
        '--plain',
        action='store_true',
        dest='vanilla',
        help='Run plain Ubuntu',
        default=False,
    ),
)

parser = OptionParser(usage, option_list=option_list)
(options, args) = parser.parse_args()

if __name__ == '__main__':
    if options.plus:
        yml, image, path = 'docker/test-plus.yml', 'amplify-agent-test-plus', 'docker/test-plus'
    elif options.vanilla:
        yml, image, path = 'docker/test-vanilla.yml', 'amplify-agent-test-vanilla', 'docker/test-vanilla'
    else:
        yml, image, path = 'docker/test.yml', 'amplify-agent-test', 'docker/test'

    shell_call('find . -name "*.pyc" -type f -delete', terminal=True)
    shell_call('cat packages/*/requirements.txt >> %s/requirements.txt' % path)
    shell_call('cp -pf %s/.dockerignore .' % path)
    shell_call('docker build -t %s -f %s/Dockerfile .' % (image, path), terminal=True)
    shell_call('rm %s/requirements.txt' % path)
    shell_call('rm .dockerignore')

    rows, columns = os.popen('stty size', 'r').read().split()
    color_print("\n= RUN TESTS =" + "="*(int(columns)-13))
    color_print("py.test test/", color="yellow")
    color_print("="*int(columns)+"\n")
    shell_call('docker-compose -f %s run test bash' % yml, terminal=True)


