from django.contrib.auth.forms import AuthenticationForm


class AuthAdminForm(AuthenticationForm):
    """
    Form for authenticating.

    Adds an Auth0 Button to log in with auth0.

    See: templates/admin/auth1_login.html
    """
    pass
