# get_permission_groups
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20Groups%28%24id%3AID%29%20%7B%0A%20%20groups%28id%3A%24id%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20null%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20Groups%28%24id%3AID%29%20%7B%0A%20%20groups%28id%3A%24id%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20null%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the list of permission groups a user can be affiliated to.
:return:

## Variables
```json
{
    "id": null
}
```
## Request
```graphql

query Groups($id:ID) {
  groups(id:$id) {
    edges {
      node {
          id
          name
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
                        "id": "R3JvdXBUeXBlOjE=",
                        "name": "administrator"
                    }
                },
                {
                    "node": {
                        "id": "R3JvdXBUeXBlOjI=",
                        "name": "editor"
                    }
                }
            ]
        }
    }
}
```
