# get_user_by_id
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20User%28%24id%3A%20ID%21%29%20%7B%0A%20%20user%28id%3A%20%24id%29%20%7B%0A%20%20%20%20id%0A%20%20%20%20username%0A%20%20%20%20firstName%0A%20%20%20%20lastName%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20User%28%24id%3A%20ID%21%29%20%7B%0A%20%20user%28id%3A%20%24id%29%20%7B%0A%20%20%20%20id%0A%20%20%20%20username%0A%20%20%20%20firstName%0A%20%20%20%20lastName%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Get user by id
Filter: *id*
The *Id* parameter can be either the sequential numeric id global ID or
the base64 encoded string (which is given in the response).

## Variables
```json
{
    "id": "VXNlclR5cGU6Mg=="
}
```
## Request
```graphql

query User($id: ID!) {
  user(id: $id) {
    id
    username
    firstName
    lastName
  }
}

```
## Response
```json
{
    "data": {
        "user": {
            "id": "VXNlclR5cGU6Mg==",
            "username": "testuser",
            "firstName": "",
            "lastName": ""
        }
    }
}
```
