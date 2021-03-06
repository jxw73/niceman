# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the niceman package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""""""

from six.moves import StringIO as SIO
from os.path import exists
from nose import SkipTest
try:
    import formatters as fmt
except ImportError:  # pragma: no cover
    # must be running from installed version where formatters is not present
    # These tests can be ran only with formatters, which is outside of the
    # niceman module space in the root of the sourcebase
    if not exists('formatters.py'):
        raise SkipTest

from niceman.cmdline.main import setup_parser
from .utils import assert_equal, ok_, assert_raises, assert_in, ok_startswith

demo_example = """
#!/bin/sh

set -e
set -u

# BOILERPLATE

HOME=IS_MY_CASTLE

#% EXAMPLE START
#
# A simple start (on the command line)
# ====================================
#
# Lorem ipsum
#%

niceman install http://the.world.com

#%
# Epilog -- with multiline rubish sdoifpwjefw
# vsdokvpsokdvpsdkv spdokvpskdvpoksd
# pfdsvja329u0fjpdsv sdpf9p93qk
#%

niceman imagine --too \\
        --much \\
        --too say \\
        yes=no

#%
# The result is not comprehensible.
#%

#% EXAMPLE END

# define shunit test cases below, or just anything desired
"""


def test_cmdline_example_to_rst():
    # don't puke on nothing
    out = fmt.cmdline_example_to_rst(SIO(''))
    out.seek(0)
    ok_startswith(out.read(), '.. AUTO-GENERATED')
    out = fmt.cmdline_example_to_rst(SIO(''), ref='dummy')
    out.seek(0)
    assert_in('.. dummy:', out.read())
    # full scale test
    out = fmt.cmdline_example_to_rst(
        SIO(demo_example), ref='mydemo')
    out.seek(0)
    assert_in('.. code-block:: sh', out.read())

def test_parser_access():
    parsers = setup_parser(return_subparsers=True)
    # we have a bunch
    ok_(len(parsers) > 3)
    assert_in('create', parsers.keys())


def test_manpage_formatter():
    addonsections = {'mytest': "uniquedummystring"}

    parsers = setup_parser(return_subparsers=True)
    for p in parsers:
        mp = fmt.ManPageFormatter(
            p, ext_sections=addonsections).format_man_page(parsers[p])
        for section in ('SYNOPSIS', 'DESCRIPTION', 'OPTIONS', 'MYTEST'):
            assert_in('.SH {0}'.format(section), mp)
        assert_in('uniquedummystring', mp)


def test_rstmanpage_formatter():
    parsers = setup_parser(return_subparsers=True)
    for p in parsers:
        mp = fmt.RSTManPageFormatter(p).format_man_page(parsers[p])
        for section in ('Synopsis', 'Description', 'Options'):
            assert_in('\n{0}'.format(section), mp)
        assert_in('{0}\n{1}'.format(p, '=' * len(p)), mp)
