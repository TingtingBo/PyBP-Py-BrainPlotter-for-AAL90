""" Tests for warnings context managers
"""
from __future__ import division, print_function, absolute_import

import sys
import warnings

import numpy as np

from nose.tools import assert_equal
from nose.tools import assert_raises
from ..testing import (error_warnings, suppress_warnings,
                       clear_and_catch_warnings, assert_allclose_safely,
                       get_fresh_mod, assert_re_in)


def assert_warn_len_equal(mod, n_in_context):
    mod_warns = mod.__warningregistry__
    # Python 3.4 appears to clear any pre-existing warnings of the same type,
    # when raising warnings inside a catch_warnings block. So, there is a
    # warning generated by the tests within the context manager, but no
    # previous warnings.
    if 'version' in mod_warns:
        assert_equal(len(mod_warns), 2)  # including 'version'
    else:
        assert_equal(len(mod_warns), n_in_context)


def test_assert_allclose_safely():
    # Test the safe version of allclose
    assert_allclose_safely([1, 1], [1, 1])
    assert_allclose_safely(1, 1)
    assert_allclose_safely(1, [1, 1])
    assert_allclose_safely([1, 1], 1 + 1e-6)
    assert_raises(AssertionError, assert_allclose_safely, [1, 1], 1 + 1e-4)
    # Broadcastable matrices
    a = np.ones((2, 3))
    b = np.ones((3, 2, 3))
    eps = np.finfo(np.float).eps
    a[0, 0] = 1 + eps
    assert_allclose_safely(a, b)
    a[0, 0] = 1 + 1.1e-5
    assert_raises(AssertionError, assert_allclose_safely, a, b)
    # Nans in same place
    a[0, 0] = np.nan
    b[:, 0, 0] = np.nan
    assert_allclose_safely(a, b)
    # Never equal with nans present, if not matching nans
    assert_raises(AssertionError,
                  assert_allclose_safely, a, b,
                  match_nans=False)
    b[0, 0, 0] = 1
    assert_raises(AssertionError, assert_allclose_safely, a, b)
    # Test allcloseness of inf, especially np.float128 infs
    for dtt in np.sctypes['float']:
        a = np.array([-np.inf, 1, np.inf], dtype=dtt)
        b = np.array([-np.inf, 1, np.inf], dtype=dtt)
        assert_allclose_safely(a, b)
        b[1] = 0
        assert_raises(AssertionError, assert_allclose_safely, a, b)
    # Empty compares equal to empty
    assert_allclose_safely([], [])


def assert_warn_len_equal(mod, n_in_context):
    mod_warns = mod.__warningregistry__
    # Python 3.4 appears to clear any pre-existing warnings of the same type,
    # when raising warnings inside a catch_warnings block. So, there is a
    # warning generated by the tests within the context manager, but no
    # previous warnings.
    if 'version' in mod_warns:
        assert_equal(len(mod_warns), 2)  # including 'version'
    else:
        assert_equal(len(mod_warns), n_in_context)


def test_clear_and_catch_warnings():
    # Initial state of module, no warnings
    my_mod = get_fresh_mod(__name__)
    assert_equal(getattr(my_mod, '__warningregistry__', {}), {})
    with clear_and_catch_warnings(modules=[my_mod]):
        warnings.simplefilter('ignore')
        warnings.warn('Some warning')
    assert_equal(my_mod.__warningregistry__, {})
    # Without specified modules, don't clear warnings during context
    with clear_and_catch_warnings():
        warnings.simplefilter('ignore')
        warnings.warn('Some warning')
    assert_warn_len_equal(my_mod, 1)
    # Confirm that specifying module keeps old warning, does not add new
    with clear_and_catch_warnings(modules=[my_mod]):
        warnings.simplefilter('ignore')
        warnings.warn('Another warning')
    assert_warn_len_equal(my_mod, 1)
    # Another warning, no module spec does add to warnings dict, except on
    # Python 3.4 (see comments in `assert_warn_len_equal`)
    with clear_and_catch_warnings():
        warnings.simplefilter('ignore')
        warnings.warn('Another warning')
    assert_warn_len_equal(my_mod, 2)


class my_cacw(clear_and_catch_warnings):
    class_modules = (sys.modules[__name__],)


def test_clear_and_catch_warnings_inherit():
    # Test can subclass and add default modules
    my_mod = get_fresh_mod(__name__)
    with my_cacw():
        warnings.simplefilter('ignore')
        warnings.warn('Some warning')
    assert_equal(my_mod.__warningregistry__, {})


def test_warn_error():
    # Check warning error context manager
    n_warns = len(warnings.filters)
    with error_warnings():
        assert_raises(UserWarning, warnings.warn, 'A test')
    with error_warnings() as w:  # w not used for anything
        assert_raises(UserWarning, warnings.warn, 'A test')
    assert_equal(n_warns, len(warnings.filters))
    # Check other errors are propagated

    def f():
        with error_warnings():
            raise ValueError('An error')
    assert_raises(ValueError, f)


def test_warn_ignore():
    # Check warning ignore context manager
    n_warns = len(warnings.filters)
    with suppress_warnings():
        warnings.warn('Here is a warning, you will not see it')
        warnings.warn('Nor this one', DeprecationWarning)
    with suppress_warnings() as w:  # w not used
        warnings.warn('Here is a warning, you will not see it')
        warnings.warn('Nor this one', DeprecationWarning)
    assert_equal(n_warns, len(warnings.filters))
    # Check other errors are propagated

    def f():
        with suppress_warnings():
            raise ValueError('An error')
    assert_raises(ValueError, f)


def test_assert_re_in():
    assert_re_in(".*", "")
    assert_re_in(".*", ["any"])

    # Should do match not search
    assert_re_in("ab", "abc")
    assert_raises(AssertionError, assert_re_in, "ab", "cab")
    assert_raises(AssertionError, assert_re_in, "ab$", "abc")

    # Sufficient to have one entry matching
    assert_re_in("ab", ["", "abc", "laskdjf"])
    assert_raises(AssertionError, assert_re_in, "ab$", ["ddd", ""])

    # Tuples should be ok too
    assert_re_in("ab", ("", "abc", "laskdjf"))
    assert_raises(AssertionError, assert_re_in, "ab$", ("ddd", ""))

    # Shouldn't "match" the empty list
    assert_raises(AssertionError, assert_re_in, "", [])
