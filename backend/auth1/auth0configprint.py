"""
Prints the configuration of the Auth0 Integration.
"""

import enum


class Application(enum.Enum):
    """
    Enumeration for the Auth0 integration Applications supported
    """

    """
    Django Backend
    """
    DJANGO = 'django'

    """
    React Web Application
    """
    REACT = 'react'

    """
    IOS Mobile Application
    """
    IOS = 'ios'

    """
    Android Mobile Application
    """
    ANDROID = 'android'


class Auth0Tenant(enum.Enum):
    """
    Enumeration for the Auth0 tenant supported
    """

    """
    Development Tenant
    """
    DEV = 'dev-yourapp'

    """
    Staging/Demo Tenant
    """
    STG = 'stg-yourapp'

    """
    Production Tenant.

    Please note that production does not use the prefix.
    """
    PRD = 'yourapp'


class Environment(enum.Enum):
    """
    Enumeration for the different environments supported
    """

    """
    Local Environment, it is mapped to the development tenant
    """
    LOCAL = 'local', Auth0Tenant.DEV

    """
    Development Environment, it is mapped to the development tenant
    """
    DEV = 'dev', Auth0Tenant.DEV

    """
    Staging Environment, it is mapped to the staging tenant
    """
    STG = 'stg', Auth0Tenant.STG

    """
    Production Environment, it is mapped to the production tenant
    """
    PRD = 'prd', Auth0Tenant.PRD

    def __new__(cls, environment, tenant: Auth0Tenant, **kwargs):
        obj = object.__new__(cls)
        obj._value = environment
        obj.tenant = tenant
        return obj


class Service(enum.Enum):
    """
    Enumeration for the Services Supported
    """

    """
    Local Django Backend Service.

    Hostnames: localhost, app.local.boilerworks.net
    Ports: 8000, 8443
    """
    LOCAL_DJANGO = (
        Environment.LOCAL,
        Application.DJANGO,
        "http://localhost:8000",
        "https://localhost:8000",
        "https://localhost:8443",
        "https://app.local.boilerworks.net:8000",
        "https://app.local.boilerworks.net:8443",
    )

    """
    Local Web Application Service:

    Hostnames: localhost, app.local.boilerworks.net
    Ports: 3000, 8443
    """
    LOCAL_REACT = (
        Environment.LOCAL,
        Application.REACT,
        "http://localhost:3000",
        "https://localhost:3000",
        "https://localhost:8443",
        "https://app.local.boilerworks.net:8443",
    )

    """
    Development Django Backend Service.

    Hostnames: app.dev.boilerworks.net
    Ports: 443
    """
    DEV_DJANGO = (
        Environment.DEV,
        Application.DJANGO,
        "https://app.dev.boilerworks.net",
        "https://app.dev.boilerworks.net:443",
    )

    DEV_REACT = (
        Environment.DEV,
        Application.REACT,
        "https://app.dev.boilerworks.net",
    )

    STG_DJANGO = (
        Environment.STG,
        Application.DJANGO,
        "https://app.stg.boilerworks.net",
        "https://app.stg.boilerworks.net:443",
    )

    STG_REACT = (
        Environment.STG,
        Application.REACT,
        "https://app.stg.boilerworks.net",
    )

    PRD_DJANGO = (
        Environment.PRD,
        Application.DJANGO,
        "https://app.boilerworks.net",
        "https://app.boilerworks.net:443",
        "https://app.prd.boilerworks.net",
        "https://app.prd.boilerworks.net:443",
    )

    PRD_REACT = (
        Environment.PRD,
        Application.REACT,
        "https://app.boilerworks.net",
        "https://app.prd.boilerworks.net",
    )

    IOS_APP = (
        Environment.DEV,
        Application.IOS,
        'com.yourapp.auth0://yourapp.us.auth0.com/ios/com.yourapp/callback'
    )

    ANDROID_APP = (
        Environment.DEV,
        Application.ANDROID,
        'com.yourapp.auth0://yourapp.us.auth0.com/android/com.yourapp/callback'
    )

    def __new__(
            cls,
            environment: Environment,
            application: Application,
            *hostnames,
            **kwargs):
        obj = object.__new__(cls)
        obj._value_ = (environment, application)
        obj.environment = environment
        obj.application = application
        obj.hostnames = list(hostnames)
        return obj


class UrlKind(enum.Flag):
    CALLBACK = enum.auto()
    LOGOUT = enum.auto()
    WEB_ORIGIN = enum.auto()


class SupportedUrls(enum.Enum):
    REACT_HOME = (
        Application.REACT,
        UrlKind.WEB_ORIGIN | UrlKind.LOGOUT,
        '',
        '/login',
        '/logout',
    )

    REACT_CALLBACK = (
        Application.REACT,
        UrlKind.CALLBACK,
        '/api/auth/callback',
    )

    DJANGO_ADMIN = (
        Application.DJANGO,
        UrlKind.WEB_ORIGIN | UrlKind.LOGOUT,
        '/app/admin/login',
    )

    DJANGO_CALLBACK = (
        Application.DJANGO,
        UrlKind.CALLBACK,
        '/app/auth1/callback'
    )

    IOS_APP = (
        Application.IOS,
        UrlKind.WEB_ORIGIN | UrlKind.LOGOUT | UrlKind.CALLBACK,
        '',
    )

    ANDROID_APP = (
        Application.ANDROID,
        UrlKind.WEB_ORIGIN | UrlKind.LOGOUT | UrlKind.CALLBACK,
        '',
    )

    def __new__(
            cls,
            application,
            url_kind: UrlKind,
            *endpoints,
            **kwargs):
        obj = object.__new__(cls)
        obj._value_ = (application, url_kind)
        obj.application = application
        obj.url_kind = url_kind
        obj.endpoints = endpoints
        return obj


def service_url_combinations(tenant: Auth0Tenant, url_kind: UrlKind):
    for environment in Environment:
        if environment.tenant != tenant:
            continue
        for service in Service:
            if service.environment != environment:
                continue
            for url in SupportedUrls:
                if url_kind not in url.url_kind:
                    continue
                if url.application != service.application:
                    continue
                # print(f'{tenant} {url_kind} {environment} {service} {url}', file=sys.stderr)
                yield service, url


def get_urls(tenant, url_kind):
    for service, url in service_url_combinations(tenant, url_kind):
        for hostname in service.hostnames:
            for endpoint in url.endpoints:
                final_url = f'{hostname}{endpoint}'
                # print(f'{service} {url}: {final_url}', file=sys.stderr)
                yield final_url


def url_combinations():
    return {
        tenant: {
            url_kind: sorted(set(get_urls(tenant, url_kind)))
            for url_kind in UrlKind
        }
        for tenant in Auth0Tenant
    }


def main():
    for tenant, url_kinds in url_combinations().items():
        print(f"# {tenant}")
        for url_kind, urls in url_kinds.items():
            print(f"## {url_kind}")
            print("```")
            print(",\n".join(urls))
            print("```")


if __name__ == '__main__':
    main()
