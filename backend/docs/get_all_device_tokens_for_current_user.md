# get_all_device_tokens_for_current_user
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20DeviceTokens%20%7B%0A%20%20devices%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20deliveryMethod%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20displayName%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20DeviceTokens%20%7B%0A%20%20devices%20%7B%0A%20%20%20%20id%0A%20%20%20%20name%0A%20%20%20%20deliveryMethod%7B%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20displayName%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Get all devices tokens for current user

## Variables
```json
{}
```
## Request
```graphql

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

```
## Response
```json
{
    "data": {
        "devices": [
            {
                "id": "RGV2aWNlVG9rZW5UeXBlOm15X2RldmljZV90b2tlbg==",
                "name": "my_device_token_name",
                "deliveryMethod": {
                    "name": "ANDROID",
                    "displayName": "Android"
                }
            }
        ]
    }
}
```
