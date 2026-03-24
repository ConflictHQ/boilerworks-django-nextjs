"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from auth1.forms import AuthAdminForm
from auth1.sessions import Auth1SessionWorkflow
from core import views
from core.dataloaders import DeferredExecutionContext
from core.schema import schema_auth
from core.utils.core_graph_ql_view import CoreGraphQLView
from core.utils.debug import autologin
from core.utils.logger_helper import gql_logger
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from graphene_django.views import GraphQLView
from graphene_file_upload.django import FileUploadGraphQLView
from pushnotif.twilio import TwilioService

from .schema import schema
from .strawberry_schema import schema as strawberry_schema, schema_auth as strawberry_schema_auth
from .views import app_root_view, metrics_view, root_view, test_open_telemetry
from core.strawberry_schema.views import CoreStrawberryView

strawberry_view = CoreStrawberryView.as_view(schema=strawberry_schema)
strawberry_auth_view = CoreStrawberryView.as_view(schema=strawberry_schema_auth)


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
    # path('silk/', include('silk.urls', namespace='silk')),
    path('sentry-debug/', trigger_error),
    path('export/', views.download_file),
    path('gql/config/upload/',
         csrf_exempt(autologin(gql_logger(FileUploadGraphQLView.as_view(graphiql=True, schema=schema))))),

    path('gql/config/', csrf_exempt(autologin(gql_logger(
        CoreGraphQLView.as_view(
            graphiql=True,
            schema=schema,
            execution_context_class=DeferredExecutionContext
        ))))),

    path('gql/config/auth/', csrf_exempt(gql_logger(
        GraphQLView.as_view(graphiql=True, schema=schema_auth))
    )),
    # Strawberry v2 endpoints (dual-mount alongside Graphene for testing)
    path('gql/v2/config/', csrf_exempt(strawberry_view)),
    path('gql/v2/config/auth/', csrf_exempt(strawberry_auth_view)),

    path('core/', include('core.urls')),
    path('pushnotif/', include('pushnotif.urls')),
    path('test/open_telemetry/', test_open_telemetry, name="test-open-telemetry"),
]

base = settings.BASE_URL
favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [

    path('', root_view),
    path(base, include(urls)),

    # Start of Auth0 Login
    path(f'{base}auth1/', include(Auth1SessionWorkflow.urls())),
    # End of Auth0 Login

    # Start of Twilio Login
    path(f'{base}twilio/', include(TwilioService.urls())),
    # End of Twilio Login

    re_path(r'^favicon\.ico$', favicon_view),
    re_path(r'^health/', include('health_check.urls')),
    path('metrics', metrics_view),

]


if settings.DEBUG:
    import warnings

    try:
        import debug_toolbar
    except ImportError:
        warnings.warn(
            "The debug toolbar was not installed. Ignore the error. \
            settings.py should already have warned the user about it."
        )
    else:
        urlpatterns += [
            re_path(r"^__debug__/", include(debug_toolbar.urls))  # type: ignore
        ]
