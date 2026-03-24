# get_current_user_profile
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0A%7B%0A%20%20me%20%7B%0A%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20lastName%0A%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20emergencyPhoneNumber%0A%20%20%20%20%20%20emergencyContactName%0A%20%20%20%20%20%20preferredContact%0A%20%20%20%20%20%20address%20%7B%0A%20%20%20%20%20%20%20%20street%0A%20%20%20%20%20%20%20%20state%0A%20%20%20%20%20%20%20%20zipcode%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0A%7B%0A%20%20me%20%7B%0A%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20lastName%0A%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20emergencyPhoneNumber%0A%20%20%20%20%20%20emergencyContactName%0A%20%20%20%20%20%20preferredContact%0A%20%20%20%20%20%20address%20%7B%0A%20%20%20%20%20%20%20%20street%0A%20%20%20%20%20%20%20%20state%0A%20%20%20%20%20%20%20%20zipcode%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the profile information from the requesting session.
:return:

## Variables
```json
{}
```
## Request
```graphql

{
  me {
    profile {
      firstName
      lastName
      phoneNumber
      emergencyPhoneNumber
      emergencyContactName
      preferredContact
      address {
        street
        state
        zipcode
      }
    }
  }
}


```
## Response
```json
{
    "data": {
        "me": {
            "profile": {
                "firstName": null,
                "lastName": null,
                "phoneNumber": null,
                "emergencyPhoneNumber": null,
                "emergencyContactName": null,
                "preferredContact": null,
                "address": null
            }
        }
    }
}
```
