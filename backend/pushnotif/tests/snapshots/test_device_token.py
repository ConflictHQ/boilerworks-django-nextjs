from core.tests.utils.base_test import BaseTest
from django.contrib.auth.models import User
from pushnotif.models import DeviceToken


class DeviceTokenTest(BaseTest):
    def setUp(self):
        super().setUp()
        from core.models import Profile
        from organization.models import OrganizationMember
        self.bmiranda, _ = User.objects.get_or_create(username='bmiranda')
        self.bmiranda.is_superuser = True
        self.bmiranda.save()
        OrganizationMember.objects.get_or_create(member=self.bmiranda, organization=self.organization)
        profile, _ = Profile.objects.get_or_create(user=self.bmiranda)
        profile.active_organization = self.organization
        profile.save()
        # Pre-create device token for the "upsert existing" test scenario
        DeviceToken.objects.get_or_create(
            device_token='my_device_token',
            defaults={'name': 'original-device', 'recipient': self.user, 'created_by': self.user}
        )

    def test_get_all_device_tokens_for_current_user(self):
        """
        # Get all devices tokens for current user
        """

        request = self.request()
        request.user = User.objects.get(username='bmiranda')
        mutation = '''
        query DeviceTokens {
          devices {
            id
            name
            deliveryMethod{
              name
              displayName
            }
          }
        }
        '''
        variables = {}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)

    def test_upsert_new_device_token(self):
        """
        # Upsert device token (Create)
        **The device token** is required and unique.
        **The name** of the device must be provided
        **The deviceOperation** defaults to SUBSCRIBE
        *The delivery method** is not required (for backwards compatibility), but should be provided
        Creates device token with the given name and token
        """

        request = self.request()
        mutation = '''
        mutation DeviceToken(
          $deviceToken: String!,
          $name: String!,
          $deliveryMethodId: delivery_method_id
        ) {
          deviceToken(
            input: {
                deviceToken: $deviceToken,
                name: $name,
                deliveryMethodId: $deliveryMethodId
            }
          ) {
            ok,
            errors{
              field
              messages
            }
          }
        }
        '''
        variables = {'deviceToken': 'new-device-token', 'name': 'user-huawei-abc123', 'deliveryMethodId': 'IOS'}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)

    def test_upsert_existing_device_token(self):
        """
        # Upsert device token (already exists)
        **The device token** is required and unique.
        **The name** of the device must be provided
        **The deviceOperation** defaults to SUBSCRIBE
        *The delivery method** is not required (to be backwards compatible), but should be provided
        If the device token is already present in the database, the mutation try to update the affiliated user
        to cover cases where users may share the same device and firebase provides the same token.
        """

        request = self.request()
        request.user = User.objects.get(username='bmiranda')
        mutation = '''
        mutation DeviceToken(
          $deviceToken: String!,
          $name: String!,
          $deliveryMethodId: delivery_method_id,
        ) {
          deviceToken(
            input: {
                deviceToken: $deviceToken,
                name: $name,
                deliveryMethodId: $deliveryMethodId
            }
          ) {
            ok,
            errors{
              field
              messages
            }
          }
        }
        '''
        variables = {'deviceToken': 'my_device_token', 'name': 'my-repeated-device', 'deliveryMethodId': 'ANDROID'}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        resulting_record = DeviceToken.objects.get(device_token='my_device_token')
        self.assertQueryResult(mutation, variables, response)
        assert resulting_record.recipient_id == request.user.id
        assert resulting_record.updated_by_id == request.user.id

    def test_delete_device_token(self):
        """
        # Delete device token
        **The device token** is required.
        **The name** of the device can be blank or null on deletions only
        **The deviceOperation** must be 'UNSUBSCRIBE'
        The device will be deleted from the database if it exists
        """

        request = self.request()
        mutation = '''
            mutation DeviceToken(
              $deviceToken: String!,
              $name: String!,
              $deviceOperation: device_operation
            ) {
              deviceToken(
                input: {
                    deviceToken: $deviceToken,
                    name: $name,
                    deviceOperation:$deviceOperation
                }
              ) {
                ok,
                errors{
                  field
                  messages
                }
              }
            }
        '''
        variables = {"deviceToken": "my-device-token", "name": "", "deviceOperation": "UNSUBSCRIBE"}
        response = self.client.execute(mutation, variables=variables, context_value=request)
        self.assertQueryResult(mutation, variables, response)
