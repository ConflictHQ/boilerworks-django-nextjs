# upsert_profile_for_given_user_fails_serialization
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%28%24userId%3AString%21%29%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%3A%7B%0A%20%20%20%20%20%20%20%20id%3A%24userId%0A%20%20%20%20%20%20%20%20email%3A%22new_em%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20birthDate%3A%221995-11-18%22%0A%20%20%20%20%20%20gender%3AMALE%0A%20%20%20%20%20%20phoneNumber%3A%22%2B18%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%22%2B18%22%0A%20%20%20%20%20%20emergencyContactName%3A%22Jane%20Doe%20Sr%22%0A%20%20%20%20%20%20preferredContact%3ASMS%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street%20543%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2219999999999999999999980808080808%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6MQ%3D%3D%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%28%24userId%3AString%21%29%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%3A%7B%0A%20%20%20%20%20%20%20%20id%3A%24userId%0A%20%20%20%20%20%20%20%20email%3A%22new_em%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20birthDate%3A%221995-11-18%22%0A%20%20%20%20%20%20gender%3AMALE%0A%20%20%20%20%20%20phoneNumber%3A%22%2B18%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%22%2B18%22%0A%20%20%20%20%20%20emergencyContactName%3A%22Jane%20Doe%20Sr%22%0A%20%20%20%20%20%20preferredContact%3ASMS%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street%20543%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2219999999999999999999980808080808%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6MQ%3D%3D%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Update fails because given profile information has formatting issues (i.e. invalid phone format)

## Variables
```json
{
    "userId": "VXNlclR5cGU6MQ=="
}
```
## Request
```graphql

mutation($userId:String!){
  profile (
    input:{
      user:{
        id:$userId
        email:"new_em"
      }
      displayName:"Jane Doe Smith"
      birthDate:"1995-11-18"
      gender:MALE
      phoneNumber:"+18"
      emergencyPhoneNumber:"+18"
      emergencyContactName:"Jane Doe Sr"
      preferredContact:SMS
      address: {
              street:"Street 543"
              state:FL
              city:"City"
              zipcode:"19999999999999999999980808080808"
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
                    "field": "address.zipcode",
                    "messages": [
                        "Ensure this field has no more than 10 characters."
                    ]
                },
                {
                    "field": "user.email",
                    "messages": [
                        "Enter a valid email address."
                    ]
                },
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
