# upsert_profile_for_given_user
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%28%24userId%3AString%21%29%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%3A%7B%0A%20%20%20%20%20%20%20%20id%3A%24userId%0A%20%20%20%20%20%20%20%20email%3A%22new_email%40boilerworks.dev%22%0A%20%20%20%20%20%20%20%20firstName%3A%22Jane%22%0A%20%20%20%20%20%20%20%20lastName%3A%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20birthDate%3A%221995-11-18%22%0A%20%20%20%20%20%20gender%3AMALE%0A%20%20%20%20%20%20phoneNumber%3A%22%2B12125552368%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%22%2B12125552368%22%0A%20%20%20%20%20%20emergencyContactName%3A%22Jane%20Doe%20Sr%22%0A%20%20%20%20%20%20preferredContact%3ASMS%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street%20543%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%28%24userId%3AString%21%29%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%3A%7B%0A%20%20%20%20%20%20%20%20id%3A%24userId%0A%20%20%20%20%20%20%20%20email%3A%22new_email%40boilerworks.dev%22%0A%20%20%20%20%20%20%20%20firstName%3A%22Jane%22%0A%20%20%20%20%20%20%20%20lastName%3A%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20birthDate%3A%221995-11-18%22%0A%20%20%20%20%20%20gender%3AMALE%0A%20%20%20%20%20%20phoneNumber%3A%22%2B12125552368%22%0A%20%20%20%20%20%20emergencyPhoneNumber%3A%22%2B12125552368%22%0A%20%20%20%20%20%20emergencyContactName%3A%22Jane%20Doe%20Sr%22%0A%20%20%20%20%20%20preferredContact%3ASMS%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street%20543%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Updates the profile information for the user that matches the provided id, with the given input.
**Note** If there is no profile in the database, then it will be created
even though this should happen when the User was added to the system.
:return:

## Variables
```json
{
    "userId": "VXNlclR5cGU6Mg=="
}
```
## Request
```graphql

mutation($userId:String!){
  profile (
    input:{
      user:{
        id:$userId
        email:"new_email@boilerworks.dev"
        firstName:"Jane"
        lastName:"Doe"
      }
      displayName:"Jane Doe Smith"
      birthDate:"1995-11-18"
      gender:MALE
      phoneNumber:"+12125552368"
      emergencyPhoneNumber:"+12125552368"
      emergencyContactName:"Jane Doe Sr"
      preferredContact:SMS
      address: {
              street:"Street 543"
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
            "ok": true,
            "errors": []
        }
    }
}
```
