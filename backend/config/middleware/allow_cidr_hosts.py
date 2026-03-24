from django.conf import settings
from django.core.exceptions import DisallowedHost
from netaddr import IPAddress, IPNetwork


class AllowCIDRHostsMiddleware:
    KNOWN_RANGES = {
        IPNetwork('10.0.0.0/8'),
    }

    KNOWN_DOMAINS = {
        '.amazonaws.com',
        '.localhost',
        '.local',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.CONFIGURATION.lower() == "local" or settings.CONFIGURATION.lower() == "tests":
            return self.get_response(request)

        host = request.get_host().split(':')[0]
        if host in settings.ALLOWED_HOSTS:
            return self.get_response(request)
        try:
            for domain in self.KNOWN_DOMAINS:
                if host.endswith(domain):
                    break
            else:
                IPAddress(host)  # Allow any IP Addresses
        except Exception:
            raise DisallowedHost(f"Invalid host: {host}")
        return self.get_response(request)
