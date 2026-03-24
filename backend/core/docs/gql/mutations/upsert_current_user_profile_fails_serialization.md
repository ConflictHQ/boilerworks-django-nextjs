# upsert_current_user_profile_fails_serialization
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%20%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%3A%22Jesus%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%3A%20%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20phoneNumber%3A%221%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%221%22%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street6134213%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%20%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%3A%22Jesus%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%3A%20%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20phoneNumber%3A%221%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%221%22%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street6134213%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


Update fails because given profile information has formatting issues (i.e. invalid phone format)
:return:

## Variables
```json
{}
```
## Request
```graphql

mutation {
  profile (
    input:{
      user : {
              firstName:"Jesus"
              lastName: "Doe"
      }
      phoneNumber:"1"
      emergencyPhoneNumber:"1"
      address: {
              street:"Street6134213"
              state:FL
              city:"City"
              zipcode:"12345-6789"
      }
  }
  ){
      ok
      errors {
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
        "profile": {
            "ok": false,
            "errors": [
                {
                    "field": "phoneNumber",
                    "messages": [
                        "The phone number entered is not valid."
                    ]
                },
                {
                    "field": "emergencyPhoneNumber",
                    "messages": [
                        "The phone number entered is not valid."
                    ]
                }
            ]
        }
    }
}
```
