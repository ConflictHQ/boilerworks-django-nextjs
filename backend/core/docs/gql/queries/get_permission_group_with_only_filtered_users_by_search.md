# get_permission_group_with_only_filtered_users_by_search
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20groups%28%24groupName%3A%20String%2C%20%24userFirst%3A%20Int%2C%20%24userSearch%3A%20String%29%20%7B%0A%20%20groups%28name%3A%20%24groupName%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20userSet%28first%3A%20%24userFirst%2C%20search%3A%20%24userSearch%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20totalCount%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22groupName%22%3A%20null%2C%0A%20%20%20%20%22userFirst%22%3A%203%2C%0A%20%20%20%20%22userSearch%22%3A%20%22testuser%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20groups%28%24groupName%3A%20String%2C%20%24userFirst%3A%20Int%2C%20%24userSearch%3A%20String%29%20%7B%0A%20%20groups%28name%3A%20%24groupName%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20userSet%28first%3A%20%24userFirst%2C%20search%3A%20%24userSearch%29%20%7B%0A%20%20%20%20%20%20%20%20%20%20totalCount%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22groupName%22%3A%20null%2C%0A%20%20%20%20%22userFirst%22%3A%203%2C%0A%20%20%20%20%22userSearch%22%3A%20%22testuser%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the permission groups alongside the users who match the provided search criteria.
:return:

## Variables
```json
{
    "groupName": null,
    "userFirst": 3,
    "userSearch": "testuser"
}
```
## Request
```graphql

query groups($groupName: String, $userFirst: Int, $userSearch: String) {
  groups(name: $groupName) {
    edges {
      node {
        id
        name
        userSet(first: $userFirst, search: $userSearch) {
          totalCount
          edges {
            node {
              username
            }
          }
        }
      }
    }
  }
}

```
## Response
```json
{
    "data": {
        "groups": {
            "edges": [
                {
                    "node": {
                        "id": "R3JvdXBUeXBlOjQ=",
                        "name": "TestGroup",
                        "userSet": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                }
            ]
        }
    }
}
```
