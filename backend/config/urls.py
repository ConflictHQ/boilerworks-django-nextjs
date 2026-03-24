"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""

from auth1.forms import AuthAdminForm
from auth1.sessions import Auth1SessionWorkflow
from core import views
from core.schema.views import CoreStrawberryView
from core.utils.debug import autologin
from core.utils.logger_helper import gql_logger
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from pushnotif.twilio import TwilioService

from .schema import schema, schema_auth
from .views import app_root_view, metrics_view, root_view, test_open_telemetry

strawberry_view = CoreStrawberryView.as_view(schema=schema)
strawberry_auth_view = CoreStrawberryView.as_view(schema=schema_auth)


def trigger_error(request):
    return 1 / 0


admin.autodiscover()
admin.site.login_form = AuthAdminForm
admin.site.login_template = 'admin/auth1_login.html'
admin.site.site_header = "App"
admin.site.site_title = f"Backend Portal. {settings.VERSION}"
admin.site.index_title = "Welcome to App Portal"

urls = [
    path('', app_root_view),

    path('admin/', admin.site.urls),
    path('nested_admin/', include('nested_admin.urls')),
    path('sentry-debug/', trigger_error),
    path('export/', views.download_file),

    # GraphQL endpoints (Strawberry) — rate limited
    path('gql/config/', csrf_exempt(autologin(gql_logger(ratelimit(key='user_or_ip', rate='100/m', block=True)(strawberry_view))))),
    path('gql/config/auth/', csrf_exempt(gql_logger(ratelimit(key='ip', rate='30/m', block=True)(strawberry_auth_view)))),
    # GraphQL WebSocket subscriptions
    path('gql/config/ws/', csrf_exempt(CoreStrawberryView.as_view(schema=schema))),

    path('core/', include('core.urls')),
    path('pushnotif/', include('pushnotif.urls')),
    path('test/open_telemetry/', test_open_telemetry, name="test-open-telemetry"),
]

base = settings.BASE_URL
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [

    path('', root_view),
    path(base, include(urls)),

    # Auth1 Login
    path(f'{base}auth1/', include(Auth1SessionWorkflow.urls())),

    # Twilio
    path(f'{base}twilio/', include(TwilioService.urls())),

    re_path(r'^favicon\.ico$', favicon_view),
    path(f'{base}metrics/', metrics_view, name='metrics'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
