# delete_device_token
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20DeviceToken%28%0A%20%20%24deviceToken%3A%20String%21%2C%0A%20%20%24name%3A%20String%21%2C%0A%20%20%24deviceOperation%3A%20device_operation%0A%29%20%7B%0A%20%20deviceToken%28%0A%20%20%20%20input%3A%20%7B%0A%20%20%20%20%20%20%20%20deviceToken%3A%20%24deviceToken%2C%0A%20%20%20%20%20%20%20%20name%3A%20%24name%2C%0A%20%20%20%20%20%20%20%20deviceOperation%3A%24deviceOperation%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%2C%0A%20%20%20%20errors%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22deviceToken%22%3A%20%22my-device-token%22%2C%0A%20%20%20%20%22name%22%3A%20%22%22%2C%0A%20%20%20%20%22deviceOperation%22%3A%20%22UNSUBSCRIBE%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20DeviceToken%28%0A%20%20%24deviceToken%3A%20String%21%2C%0A%20%20%24name%3A%20String%21%2C%0A%20%20%24deviceOperation%3A%20device_operation%0A%29%20%7B%0A%20%20deviceToken%28%0A%20%20%20%20input%3A%20%7B%0A%20%20%20%20%20%20%20%20deviceToken%3A%20%24deviceToken%2C%0A%20%20%20%20%20%20%20%20name%3A%20%24name%2C%0A%20%20%20%20%20%20%20%20deviceOperation%3A%24deviceOperation%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%2C%0A%20%20%20%20errors%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22deviceToken%22%3A%20%22my-device-token%22%2C%0A%20%20%20%20%22name%22%3A%20%22%22%2C%0A%20%20%20%20%22deviceOperation%22%3A%20%22UNSUBSCRIBE%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Delete device token
**The device token** is required.
**The name** of the device can be blank or null on deletions only
**The deviceOperation** must be 'UNSUBSCRIBE'
The device will be deleted from the database if it exists

## Variables
```json
{
    "deviceToken": "my-device-token",
    "name": "",
    "deviceOperation": "UNSUBSCRIBE"
}
```
## Request
```graphql

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
