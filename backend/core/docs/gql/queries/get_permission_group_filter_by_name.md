# get_permission_group_filter_by_name
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20groups%20%7B%0A%20%20groups%28name%3A%22Platform%22%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22name%22%3A%20%22adm%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20groups%20%7B%0A%20%20groups%28name%3A%22Platform%22%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22name%22%3A%20%22adm%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Returns the permission groups which names are similar to the given string.
:return:

## Variables
```json
{
    "name": "adm"
}
```
## Request
```graphql

query groups {
  groups(name:"Platform") {
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
            "edges": []
        }
    }
}
```
