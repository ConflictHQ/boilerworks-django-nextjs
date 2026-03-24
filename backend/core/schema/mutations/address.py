import logging

import graphene
from core.models import Address
from core.schema.mutations.common import UtilityForm
from django import forms

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    'required': 'This field is required',
    'invalid': 'Enter a valid name'
}


class AddressForm(UtilityForm, forms.ModelForm):
    class Meta:
        model = Address
        exclude = 'version', 'created_by', 'created_at', 'updated_at', 'updated_by'


class AddressInput(graphene.InputObjectType):
    street = graphene.String(required=False)
    state = graphene.String(required=False)
    city = graphene.String(required=False)
    county = graphene.String(required=False)
    zipcode = graphene.String(required=False)
    suiteUnit = graphene.String(required=False)


UtilityForm.register_form(AddressInput, AddressForm)
