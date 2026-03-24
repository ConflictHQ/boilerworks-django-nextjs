# update_organization_member_status
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20%28%24userId%3A%20String%21%2C%20%24isActive%3A%20Boolean%21%29%20%7B%0A%20%20organizationMemberStatus%28input%3A%20%7BuserId%3A%20%24userId%2C%20isActive%3A%20%24isActive%7D%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%2C%0A%20%20%20%20%22isActive%22%3A%20false%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20%28%24userId%3A%20String%21%2C%20%24isActive%3A%20Boolean%21%29%20%7B%0A%20%20organizationMemberStatus%28input%3A%20%7BuserId%3A%20%24userId%2C%20isActive%3A%20%24isActive%7D%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6Mg%3D%3D%22%2C%0A%20%20%20%20%22isActive%22%3A%20false%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Updates User *is_active* status
**The UserId** of the target user is required.
**The isActive** field is required.
**OrganizationId** is optional, defaults to the requester's active organization
Updates the is_active flag for both the OrganizationMember entry and the User model.

## Variables
```json
{
    "userId": "VXNlclR5cGU6Mg==",
    "isActive": false
}
```
## Request
```graphql

mutation ($userId: String!, $isActive: Boolean!) {
  organizationMemberStatus(input: {userId: $userId, isActive: $isActive}) {
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
        "organizationMemberStatus": {
            "ok": true,
            "errors": []
        }
    }
}
```
