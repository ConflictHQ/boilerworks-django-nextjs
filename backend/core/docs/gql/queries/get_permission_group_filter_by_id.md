# get_permission_group_filter_by_id
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20Groups%28%24id%3AID%29%20%7B%0A%20%20groups%28id%3A%24id%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20userSet%20%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20%22R3JvdXBUeXBlOjQ%3D%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20Groups%28%24id%3AID%29%20%7B%0A%20%20groups%28id%3A%24id%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20userSet%20%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20username%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20firstName%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20lastName%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22id%22%3A%20%22R3JvdXBUeXBlOjQ%3D%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the permission group for the given id.
:return:

## Variables
```json
{
    "id": "R3JvdXBUeXBlOjQ="
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
          userSet  {
            edges {
              node {
                id
                username
                firstName
                lastName
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
                            "edges": []
                        }
                    }
                }
            ]
        }
    }
}
```
