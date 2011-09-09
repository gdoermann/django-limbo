"""
Optional Settings:
    TEST_EXCLUDE: A list of apps to exclude by default from testing
    RUN_ALL_TESTS: Overrides exclude and runs all tests (default: False - which uses the TEST_EXCLUDE)
    TEST_FIXTURES: A list of fixtures to load when testing.

"""
import unittest
from django.core.management import call_command
from django.db.models.loading import get_app, get_apps
from django.test.simple import DjangoTestSuiteRunner, build_test, reorder_suite, build_suite, TestCase
import logging
from django import http
from django.conf import settings
from django.forms.models import model_to_dict
from django.test.client import Client, MULTIPART_CONTENT
from limbo.strings import unique_string

log = logging.getLogger(__file__)
EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])
TESTING_NOT_IMPLEMENTED_FAIL = getattr(settings, 'TESTING_NOT_IMPLEMENTED_FAIL', True)

_test_run = 0
class BaseTestCase(unittest.TestCase):
    password = 'qwerty'

    def setUp(self):
        global _test_run
        _test_run += 1
        self._test_run = _test_run

    def not_implemented(self, msg = "Test not Implemented"):
        if TESTING_NOT_IMPLEMENTED_FAIL:
            raise NotImplementedError(msg)
    def post_not_implemented(self):
        self.not_implemented("POST test not implemented")


class ViewTestCase(BaseTestCase):
    AUTO_TEST_LINKS = True
    class CODES:
        success = http.HttpResponse.status_code
        redirect = http.HttpResponseRedirect.status_code
        permanent_redirect = http.HttpResponsePermanentRedirect.status_code
        not_modified = http.HttpResponseNotModified.status_code
        bad_request = http.HttpResponseBadRequest.status_code
        not_found = http.HttpResponseNotFound.status_code
        forbidden = http.HttpResponseForbidden.status_code
        not_allowed = http.HttpResponseNotAllowed.status_code
        gone = http.HttpResponseGone.status_code
        error = http.HttpResponseServerError.status_code

    def setUp(self):
        # Every test needs a client.
        super(ViewTestCase, self).setUp()
        self.client = Client()

    def get(self, path, data={}, follow=False, **extra):
        return self.client.get(path, data, follow, **extra)

    def get_ajax(self, path, data = {}, follow = False, **extra):
        extra['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.get(path, data, follow, **extra)

    def post(self, path, data={}, content_type=MULTIPART_CONTENT, follow=False, **extra):
        return self.client.post(path, data, content_type, follow, **extra)

    def post_ajax(self, path, data={}, content_type=MULTIPART_CONTENT, follow=False, **extra):
        extra['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        return self.post(path, data, content_type, follow, **extra)

    def _user_login(self, user, password = None):
        self.logout()
        password = password or self.password
        success = self.client.login(username=user.username, password=password)
        self.failUnless(success, 'Failed to login')
        return success

    def logout(self):
        self.client.logout()

    def model_dict(self, instance, fields = None, exclude = None):
        return model_to_dict(instance, fields, exclude)

class AdvancedTestSuiteRunner(DjangoTestSuiteRunner):
    def __init__(self, *args, **kwargs):
        from django.conf import settings
        settings.IS_TESTRUN = True
        settings.TESTING = True
        south_log = logging.getLogger("south")
        south_log.setLevel(logging.WARNING)
        super(AdvancedTestSuiteRunner, self).__init__(*args, **kwargs)

    def setup_databases(self, **kwargs):
        databases = super(AdvancedTestSuiteRunner, self).setup_databases(**kwargs)
        self.load_fixtures()
        return databases

    def load_fixtures(self):
        for fixture in getattr(settings, 'TEST_FIXTURES', []):
            call_command('loaddata', fixture)

    def build_suite(self, *args, **kwargs):
        suite = self.safe_build_suite(*args, **kwargs)
        if not args[0] and not getattr(settings, 'RUN_ALL_TESTS', False):
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg not in EXCLUDED_APPS:
                    tests.append(case)
            suite._tests = tests
        return suite

    def safe_build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = unittest.TestSuite()

        if test_labels:
            for label in test_labels:
                try:
                    if '.' in label:
                        suite.addTest(build_test(label))
                    else:
                        app = get_app(label)
                        suite.addTest(build_suite(app))
                except Exception:
                    log.warning("Could not add test for label: %s" %label)
        else:
            for app in get_apps():
                try:
                    suite.addTest(build_suite(app))
                except Exception:
                    log.warning("Could not add tests for app: %s" %app)

        if extra_tests:
            for test in extra_tests:
                suite.addTest(test)

        return reorder_suite(suite, (TestCase,))

