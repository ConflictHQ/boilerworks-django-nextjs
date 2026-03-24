# get_current_user
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20Me%20%7B%0A%20%20me%20%7B%0A%20%20%20%20username%0A%20%20%20%20email%0A%20%20%20%20firstName%0A%20%20%20%20isActive%0A%20%20%20%20lastName%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20Me%20%7B%0A%20%20me%20%7B%0A%20%20%20%20username%0A%20%20%20%20email%0A%20%20%20%20firstName%0A%20%20%20%20isActive%0A%20%20%20%20lastName%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the user information from the requesting session.
:return:

## Variables
```json
{}
```
## Request
```graphql

query Me {
  me {
    username
    email
    firstName
    isActive
    lastName
  }
}

```
## Response
```json
{
    "data": {
        "me": {
            "username": "test_superuser",
            "email": "superuser@boilerworks.dev",
            "firstName": "test",
            "isActive": true,
            "lastName": "superuser"
        }
    }
}
```
