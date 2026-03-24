"""
Tests for rate limiting on auth endpoints.

Two layers are verified:
1. RatelimitMiddleware.process_exception converts Ratelimited to HTTP 403.
2. The rate-limit decorator blocks a client IP after the configured limit.

We use RequestFactory directly to avoid full middleware-stack issues in the
test environment (the debug toolbar has no registered URL namespace here).
"""
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django_ratelimit.middleware import RatelimitMiddleware

_FRESH_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-test',
    }
}


class RateLimitMiddlewareTest(TestCase):
    """RatelimitMiddleware.process_exception converts Ratelimited to HTTP 403."""

    def _middleware(self):
        return RatelimitMiddleware(lambda req: HttpResponse('ok'))

    def test_ratelimited_exception_returns_403(self):
        request = RequestFactory().post('/app/auth1/session')
        response = self._middleware().process_exception(request, Ratelimited())
        self.assertEqual(response.status_code, 403)

    def test_unrelated_exception_returns_none(self):
        request = RequestFactory().get('/')
        result = self._middleware().process_exception(request, ValueError("not rate limited"))
        self.assertIsNone(result)


@override_settings(CACHES=_FRESH_CACHE)
class RateLimitDecoratorTest(TestCase):
    """Rate-limit decorator blocks a given IP after the configured number of requests."""

    def setUp(self):
        cache.clear()

    def _make_view(self, rate):
        """Return a POST view wrapped with the ratelimit decorator at *rate*."""
        @ratelimit(key='ip', rate=rate, method='POST', block=True)
        def view(request):
            return HttpResponse('ok')
        return view

    def test_requests_within_limit_succeed(self):
        view = self._make_view('5/m')
        factory = RequestFactory()
        for _ in range(5):
            request = factory.post('/', REMOTE_ADDR='10.0.0.1')
            response = view(request)
            self.assertEqual(response.status_code, 200)

    def test_request_beyond_limit_raises_ratelimited(self):
        view = self._make_view('5/m')
        factory = RequestFactory()
        for _ in range(5):
            factory.post('/', REMOTE_ADDR='10.0.0.2')
            view(factory.post('/', REMOTE_ADDR='10.0.0.2'))
        with self.assertRaises(Ratelimited):
            view(factory.post('/', REMOTE_ADDR='10.0.0.2'))

    def test_different_ips_have_independent_counters(self):
        view = self._make_view('1/m')
        factory = RequestFactory()
        # Exhaust the limit for IP A.
        view(factory.post('/', REMOTE_ADDR='10.0.0.3'))
        with self.assertRaises(Ratelimited):
            view(factory.post('/', REMOTE_ADDR='10.0.0.3'))
        # IP B should still be allowed.
        response = view(factory.post('/', REMOTE_ADDR='10.0.0.4'))
        self.assertEqual(response.status_code, 200)
