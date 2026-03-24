# get_site_labels_filter_by_prefix
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20siteLabels%28%24key%3A%20String%2C%20%24locale%3AString%29%20%7B%0A%20%20siteLabels%28key%3A%24key%2C%20locale%3A%24locale%29%20%7B%0A%20%20%20%20totalCount%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20key%0A%20%20%20%20%20%20%20%20text%0A%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22key%22%3A%20%22company_info.management%22%2C%0A%20%20%20%20%22locale%22%3A%20null%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20siteLabels%28%24key%3A%20String%2C%20%24locale%3AString%29%20%7B%0A%20%20siteLabels%28key%3A%24key%2C%20locale%3A%24locale%29%20%7B%0A%20%20%20%20totalCount%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20key%0A%20%20%20%20%20%20%20%20text%0A%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D%0A&variables=%7B%0A%20%20%20%20%22key%22%3A%20%22company_info.management%22%2C%0A%20%20%20%20%22locale%22%3A%20null%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


# Get site labels by key (or prefix)
Returns all the site labels that match the given key as a prefix.
i.e. for the key about_page, you will get both about_page.title and about_page.description

## Variables
```json
{
    "key": "company_info.management",
    "locale": null
}
```
## Request
```graphql

query siteLabels($key: String, $locale:String) {
  siteLabels(key:$key, locale:$locale) {
    totalCount
    edges {
      node {
        key
        text

      }
    }
  }
}

```
## Response
```json
{
    "data": {
        "siteLabels": {
            "totalCount": 0,
            "edges": []
        }
    }
}
```
