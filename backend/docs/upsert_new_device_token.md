# upsert_new_device_token
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20DeviceToken%28%0A%20%20%24deviceToken%3A%20String%21%2C%0A%20%20%24name%3A%20String%21%2C%0A%20%20%24deliveryMethodId%3A%20delivery_method_id%0A%29%20%7B%0A%20%20deviceToken%28%0A%20%20%20%20input%3A%20%7B%0A%20%20%20%20%20%20%20%20deviceToken%3A%20%24deviceToken%2C%0A%20%20%20%20%20%20%20%20name%3A%20%24name%2C%0A%20%20%20%20%20%20%20%20deliveryMethodId%3A%20%24deliveryMethodId%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%2C%0A%20%20%20%20errors%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22deviceToken%22%3A%20%22new-device-token%22%2C%0A%20%20%20%20%22name%22%3A%20%22user-huawei-abc123%22%2C%0A%20%20%20%20%22deliveryMethodId%22%3A%20%22IOS%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20DeviceToken%28%0A%20%20%24deviceToken%3A%20String%21%2C%0A%20%20%24name%3A%20String%21%2C%0A%20%20%24deliveryMethodId%3A%20delivery_method_id%0A%29%20%7B%0A%20%20deviceToken%28%0A%20%20%20%20input%3A%20%7B%0A%20%20%20%20%20%20%20%20deviceToken%3A%20%24deviceToken%2C%0A%20%20%20%20%20%20%20%20name%3A%20%24name%2C%0A%20%20%20%20%20%20%20%20deliveryMethodId%3A%20%24deliveryMethodId%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%2C%0A%20%20%20%20errors%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22deviceToken%22%3A%20%22new-device-token%22%2C%0A%20%20%20%20%22name%22%3A%20%22user-huawei-abc123%22%2C%0A%20%20%20%20%22deliveryMethodId%22%3A%20%22IOS%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Upsert device token (Create)
**The device token** is required and unique.
**The name** of the device must be provided
**The deviceOperation** defaults to SUBSCRIBE
*The delivery method** is not required (for backwards compatibility), but should be provided
Creates device token with the given name and token

## Variables
```json
{
    "deviceToken": "new-device-token",
    "name": "user-huawei-abc123",
    "deliveryMethodId": "IOS"
}
```
## Request
```graphql

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

```
## Response
```json
{
    "data": {
        "deviceToken": {
            "ok": true,
            "errors": []
        }
    }
}
```
