# get_all_delivery_method_templates
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20DeliveryMethodTemplates%20%7B%0A%20%20deliveryMethodTemplates%20%7B%0A%20%20%20%20userNotificationConfig%20%7B%0A%20%20%20%20%20%20isEnabled%0A%20%20%20%20%7D%0A%20%20%20%20deliveryMethod%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20notificationTemplate%20%7B%0A%20%20%20%20%20%20displayName%0A%20%20%20%20%7D%0A%20%20%20%20neverSendNotification%0A%20%20%20%20alwaysSendNotification%0A%20%20%20%20id%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20DeliveryMethodTemplates%20%7B%0A%20%20deliveryMethodTemplates%20%7B%0A%20%20%20%20userNotificationConfig%20%7B%0A%20%20%20%20%20%20isEnabled%0A%20%20%20%20%7D%0A%20%20%20%20deliveryMethod%20%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%7D%0A%20%20%20%20notificationTemplate%20%7B%0A%20%20%20%20%20%20displayName%0A%20%20%20%20%7D%0A%20%20%20%20neverSendNotification%0A%20%20%20%20alwaysSendNotification%0A%20%20%20%20id%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Get all delivery method templates
Displays the structure and the configuration of each notification message per delivery method

## Variables
```json
{}
```
## Request
```graphql

query DeliveryMethodTemplates {
  deliveryMethodTemplates {
    userNotificationConfig {
      isEnabled
    }
    deliveryMethod {
      name
    }
    notificationTemplate {
      displayName
    }
    neverSendNotification
    alwaysSendNotification
    id
  }
}

```
## Response
```json
{
    "data": {
        "deliveryMethodTemplates": [
            {
                "userNotificationConfig": {
                    "isEnabled": true
                },
                "deliveryMethod": {
                    "name": "ANDROID"
                },
                "notificationTemplate": {
                    "displayName": "Test Message received"
                },
                "neverSendNotification": false,
                "alwaysSendNotification": false,
                "id": "RGVsaXZlcnlNZXRob2ROb3RpZmljYXRpb25UZW1wbGF0ZVR5cGU6MQ=="
            },
            {
                "userNotificationConfig": {
                    "isEnabled": true
                },
                "deliveryMethod": {
                    "name": "IOS"
                },
                "notificationTemplate": {
                    "displayName": "Test Message received"
                },
                "neverSendNotification": false,
                "alwaysSendNotification": false,
                "id": "RGVsaXZlcnlNZXRob2ROb3RpZmljYXRpb25UZW1wbGF0ZVR5cGU6Mg=="
            }
        ]
    }
}
```
