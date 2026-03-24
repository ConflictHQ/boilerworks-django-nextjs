# should_get_all_components
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20Components%20%7B%0A%20%20components%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20Components%20%7B%0A%20%20components%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Retrieve all ui components
    Permissions affect visibility, if you don't have access to
    a component it won't show on the query results

## Variables
```json
{}
```
## Request
```graphql

query Components {
  components {
    edges {
      node {
        name
        id
      }
    }
  }
}

```
## Response
```json
{
    "data": {
        "components": {
            "edges": [
                {
                    "node": {
                        "name": "Navigation",
                        "id": "Q29tcG9uZW50VHlwZTox"
                    }
                },
                {
                    "node": {
                        "name": "Dashboard",
                        "id": "Q29tcG9uZW50VHlwZToy"
                    }
                }
            ]
        }
    }
}
```
