# update_ui_component_invalid_order_sequence
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Amutation%20Component%20%7B%0A%20%20component%20%28input%20%3A%7B%0A%20%20%20%20id%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20name%3A%20%22my_componentupdated%22%0A%20%20%20%20path%3A%20%22%2Fmy-componentupdated%22%0A%20%20%20%20slug%3A%20%22mycomponentupdated%22%0A%20%20%20%20description%3A%22component%20for%20testing%20upadted%22%0A%20%20%20%20properties%3A%20%22%7B%5C%22title%5C%22%3A%20%5C%22Test%20Title%20updated%5C%22%2C%20%5C%22description%5C%22%3A%20%5C%22Test%20Description%5C%22%7D%22%0A%20%20%20%20children%20%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A0%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A99%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZTo1%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%20%20%7D%29%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Amutation%20Component%20%7B%0A%20%20component%20%28input%20%3A%7B%0A%20%20%20%20id%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20name%3A%20%22my_componentupdated%22%0A%20%20%20%20path%3A%20%22%2Fmy-componentupdated%22%0A%20%20%20%20slug%3A%20%22mycomponentupdated%22%0A%20%20%20%20description%3A%22component%20for%20testing%20upadted%22%0A%20%20%20%20properties%3A%20%22%7B%5C%22title%5C%22%3A%20%5C%22Test%20Title%20updated%5C%22%2C%20%5C%22description%5C%22%3A%20%5C%22Test%20Description%5C%22%7D%22%0A%20%20%20%20children%20%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A0%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZToy%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20sortOrder%3A99%2C%0A%20%20%20%20%20%20%20%20childComponent%3A%20%22Q29tcG9uZW50VHlwZTo1%22%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%20%20%7D%29%7B%0A%20%20%20%20ok%0A%20%20%20%20errors%20%7B%0A%20%20%20%20%20%20messages%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%7D)

<sup>*\*You may need to update the url host and port*</sub>


## Update UI component fails due to invalid order sequence
    Provided sorting order for components must be a positive numeric
    sequence starting from zero and increasing by 1


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
    description:"component for testing upadted"
    properties: "{\"title\": \"Test Title updated\", \"description\": \"Test Description\"}"
    children : [
      {
        sortOrder:0,
        childComponent: "Q29tcG9uZW50VHlwZToy"
      }
      {
        sortOrder:99,
        childComponent: "Q29tcG9uZW50VHlwZTo1"
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
    "errors": [
        {
            "message": "[ErrorDetail(string='sort_order must be a positive numeric sequence from zero.', code='invalid')]",
            "locations": [
                {
                    "line": 3,
                    "column": 15
                }
            ],
            "path": [
                "component"
            ]
        }
    ],
    "data": {
        "component": null
    }
}
```
