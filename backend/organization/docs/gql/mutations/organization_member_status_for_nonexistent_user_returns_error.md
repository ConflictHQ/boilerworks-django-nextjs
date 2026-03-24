# organization_member_status_for_nonexistent_user_returns_error
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20%28%24userId%3A%20String%21%2C%20%24isActive%3A%20Boolean%21%29%20%7B%0A%20%20organizationMemberStatus%28input%3A%20%7BuserId%3A%20%24userId%2C%20isActive%3A%20%24isActive%7D%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6OTk5OTk5OQ%3D%3D%22%2C%0A%20%20%20%20%22isActive%22%3A%20false%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20%28%24userId%3A%20String%21%2C%20%24isActive%3A%20Boolean%21%29%20%7B%0A%20%20organizationMemberStatus%28input%3A%20%7BuserId%3A%20%24userId%2C%20isActive%3A%20%24isActive%7D%29%20%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20field%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6OTk5OTk5OQ%3D%3D%22%2C%0A%20%20%20%20%22isActive%22%3A%20false%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>

organizationMemberStatus mutation returns a GQL error when the userId doesn't exist.
## Variables
```json
{
    "userId": "VXNlclR5cGU6OTk5OTk5OQ==",
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
    "errors": [
        {
            "message": "VXNlclR5cGU6OTk5OTk5OQ== is not a member of organization T3JnYW5pemF0aW9uVHlwZTo0OA==",
            "locations": [
                {
                    "line": 3,
                    "column": 11
                }
            ],
            "path": [
                "organizationMemberStatus"
            ]
        }
    ],
    "data": {
        "organizationMemberStatus": null
    }
}
```
