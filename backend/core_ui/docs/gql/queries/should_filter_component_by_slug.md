# should_filter_component_by_slug
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20Components%28%24slug%3A%20String%21%29%20%7B%0A%20%20components%28slug%3A%20%24slug%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20components%20%7B%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20guid%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22slug%22%3A%20%22dashboard%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20Components%28%24slug%3A%20String%21%29%20%7B%0A%20%20components%28slug%3A%20%24slug%29%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20id%0A%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20components%20%7B%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20slug%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20guid%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22slug%22%3A%20%22dashboard%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Filter component by slug

   Filter: *slug*: of the component to retrieved

## Variables
```json
{
    "slug": "dashboard"
}
```
## Request
```graphql

query Components($slug: String!) {
  components(slug: $slug) {
    edges {
      node {
        id
        slug
        components {
          edges {
            node {
              slug
              guid
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
        "components": {
            "edges": []
        }
    }
}
```
