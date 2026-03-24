# generate_rocket_chat_token
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20CreateRocketchatTokenMutation%7B%0A%20%20generateRocketChatToken%20%7B%0A%20%20%20%20token%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20CreateRocketchatTokenMutation%7B%0A%20%20generateRocketChatToken%20%7B%0A%20%20%20%20token%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Requests rocket chat token for login
Creates rocket chat token for a user,
 if the user does not have a rocket chat account it is created as part of the same request.
:return: the authentication token to be used for the rocket chat

## Variables
```json
{}
```
## Request
```graphql

mutation CreateRocketchatTokenMutation{
  generateRocketChatToken {
    token
  }
}

```
## Response
```json
{
    "data": {
        "generateRocketChatToken": {
            "token": "abc"
        }
    }
}
```
