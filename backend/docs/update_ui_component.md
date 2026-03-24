# update_ui_component
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20Component%20%7B%0A%20%20component%20%28input%20%3A%7B%0A%20%20%20%20id%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20name%3A%20%22my_componentupdated%22%0A%20%20%20%20path%3A%20%22%2Fmy-componentupdated%22%0A%20%20%20%20slug%3A%20%22mycomponentupdated%22%0A%20%20%20%20description%3A%22component%20for%20testing%20updated%22%0A%20%20%20%20properties%3A%20%22%7B%5C%22title%5C%22%3A%20%5C%22Test%20Title%20updated%5C%22%2C%20%5C%22description%5C%22%3A%20%5C%22Test%20Description%5C%22%7D%22%0A%20%20%20%20children%20%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A0%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%20%20%7D%29%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20Component%20%7B%0A%20%20component%20%28input%20%3A%7B%0A%20%20%20%20id%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20name%3A%20%22my_componentupdated%22%0A%20%20%20%20path%3A%20%22%2Fmy-componentupdated%22%0A%20%20%20%20slug%3A%20%22mycomponentupdated%22%0A%20%20%20%20description%3A%22component%20for%20testing%20updated%22%0A%20%20%20%20properties%3A%20%22%7B%5C%22title%5C%22%3A%20%5C%22Test%20Title%20updated%5C%22%2C%20%5C%22description%5C%22%3A%20%5C%22Test%20Description%5C%22%7D%22%0A%20%20%20%20children%20%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A0%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%20%20%7D%29%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Update UI component mutation

   If ID is given, it will update the component, otherwise it will create a new one

## Variables
```json
{}
```
## Request
```graphql

mutation Component {
  component (input :{
    id: "Q29tcG9uZW50VHlwZToy"
    name: "my_componentupdated"
    path: "/my-componentupdated"
    slug: "mycomponentupdated"
    description:"component for testing updated"
    properties: "{\"title\": \"Test Title updated\", \"description\": \"Test Description\"}"
    children : [
      {
        sortOrder:0,
        childComponent: "Q29tcG9uZW50VHlwZToy"
      }
    ]
  }){
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
        "component": {
            "ok": true,
            "errors": []
        }
    }
}
```
