from django import forms


class MagicTokenForm(forms.Form):
    token = forms.CharField()
