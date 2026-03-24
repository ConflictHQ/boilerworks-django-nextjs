# upsert_current_user_profile
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%20%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%3A%22Jesus%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%3A%20%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street6134213%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20%7B%0A%20%20profile%20%28%0A%20%20%20%20input%3A%7B%0A%20%20%20%20%20%20user%20%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%3A%22Jesus%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%3A%20%22Doe%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20displayName%3A%22Jane%20Doe%20Smith%22%0A%20%20%20%20%20%20address%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20street%3A%22Street6134213%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20state%3AFL%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20city%3A%22City%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20zipcode%3A%2212345-6789%22%0A%20%20%20%20%20%20%7D%0A%20%20%7D%0A%20%20%29%7B%0A%20%20%20%20%20%20ok%0A%20%20%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20%20%20field%0A%20%20%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


Updates the profile information for the current user, with the given input.
**Note** If there is no profile in the database, then it will be created
even though this should happen when the User was added to the system.
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
      displayName:"Jane Doe Smith"
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
            "ok": true,
            "errors": []
        }
    }
}
```
