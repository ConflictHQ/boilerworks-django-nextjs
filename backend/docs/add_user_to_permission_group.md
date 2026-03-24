# add_user_to_permission_group
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20permissionGroupOperation%28%0A%20%20%20%20%24userIds%3A%20%5BString%5D%21%0A%20%20%20%20%24groupId%3A%20String%21%0A%20%20%20%20%24operation%3A%20operation%21%0A%29%7B%0A%20%20permissionGroupOperation%28%0A%20%20%20%20input%20%3A%20%7B%0A%20%20%20%20%20%20userIds%3A%20%24userIds%0A%20%20%20%20%20%20groupId%3A%20%24groupId%0A%20%20%20%20%20%20operation%3A%20%24operation%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userIds%22%3A%20%5B%0A%20%20%20%20%20%20%20%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%20%20%20%20%5D%2C%0A%20%20%20%20%22groupId%22%3A%20%22R3JvdXBUeXBlOjI%3D%22%2C%0A%20%20%20%20%22operation%22%3A%20%22ADD%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20permissionGroupOperation%28%0A%20%20%20%20%24userIds%3A%20%5BString%5D%21%0A%20%20%20%20%24groupId%3A%20String%21%0A%20%20%20%20%24operation%3A%20operation%21%0A%29%7B%0A%20%20permissionGroupOperation%28%0A%20%20%20%20input%20%3A%20%7B%0A%20%20%20%20%20%20userIds%3A%20%24userIds%0A%20%20%20%20%20%20groupId%3A%20%24groupId%0A%20%20%20%20%20%20operation%3A%20%24operation%0A%20%20%20%20%7D%0A%20%20%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userIds%22%3A%20%5B%0A%20%20%20%20%20%20%20%20%22VXNlclR5cGU6Mg%3D%3D%22%0A%20%20%20%20%5D%2C%0A%20%20%20%20%22groupId%22%3A%20%22R3JvdXBUeXBlOjI%3D%22%2C%0A%20%20%20%20%22operation%22%3A%20%22ADD%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Adds user to the provided permission group.
:return:

## Variables
```json
{
    "userIds": [
        "VXNlclR5cGU6Mg=="
    ],
    "groupId": "R3JvdXBUeXBlOjI=",
    "operation": "ADD"
}
```
## Request
```graphql

mutation permissionGroupOperation(
    $userIds: [String]!
    $groupId: String!
    $operation: operation!
){
  permissionGroupOperation(
    input : {
      userIds: $userIds
      groupId: $groupId
      operation: $operation
    }
  ) {
    ok
    errors {
      messages
    }
  }
}

```
## Response
```json
{
    "data": {
        "permissionGroupOperation": {
            "ok": true,
            "errors": []
        }
    }
}
```
