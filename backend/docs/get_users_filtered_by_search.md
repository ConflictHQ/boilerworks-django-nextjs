# get_users_filtered_by_search
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20users%28%24first%3A%20Int%2C%20%24search%3A%20String%29%20%7B%0A%20%20users%28first%3A%20%24first%2C%20search%3A%20%24search%29%20%7B%0A%20%20%20%20totalCount%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22first%22%3A%203%2C%0A%20%20%20%20%22search%22%3A%20%22test_superuser%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20users%28%24first%3A%20Int%2C%20%24search%3A%20String%29%20%7B%0A%20%20users%28first%3A%20%24first%2C%20search%3A%20%24search%29%20%7B%0A%20%20%20%20totalCount%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22first%22%3A%203%2C%0A%20%20%20%20%22search%22%3A%20%22test_superuser%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Get users by search
Filter: *search*
The result will be the list of users whose username, email, firstname or lastname matches the search.

## Variables
```json
{
    "first": 3,
    "search": "test_superuser"
}
```
## Request
```graphql

query users($first: Int, $search: String) {
  users(first: $first, search: $search) {
    totalCount
    edges {
      node {
        username
        firstName
      }
    }
  }
}

```
## Response
```json
{
    "data": {
        "users": {
            "totalCount": 1,
            "edges": [
                {
                    "node": {
                        "username": "test_superuser",
                        "firstName": "test"
                    }
                }
            ]
        }
    }
}
```
