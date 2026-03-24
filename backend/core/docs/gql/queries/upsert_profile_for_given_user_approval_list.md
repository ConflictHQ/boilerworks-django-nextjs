# upsert_profile_for_given_user_approval_list
### See in GraphiQl!
- [Dev](https://app.dev.boilerworks.net/app/gql/config/#query=%0Aquery%20GetPendingApprovals%20%7B%0A%0A%20%20approvalRequestPolicies%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20permission%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20requests%20%7B%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20parent%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%0A%20%20approvalRequests%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20policy%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20permission%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20codename%0A%20%20%20%20%20%20%20%20%20%20%20%20contentType%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20appLabel%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20model%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20parent%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6MQ%3D%3D%22%0A%7D)
- [Local](http://localhost:8000/app/gql/config/#query=%0Aquery%20GetPendingApprovals%20%7B%0A%0A%20%20approvalRequestPolicies%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20permission%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20requests%20%7B%0A%20%20%20%20%20%20%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20parent%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%0A%20%20approvalRequests%20%7B%0A%20%20%20%20edges%20%7B%0A%20%20%20%20%20%20node%20%7B%0A%20%20%20%20%20%20%20%20policy%20%7B%0A%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20permission%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20name%0A%20%20%20%20%20%20%20%20%20%20%20%20codename%0A%20%20%20%20%20%20%20%20%20%20%20%20contentType%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20appLabel%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20model%0A%20%20%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20profile%20%7B%0A%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20parent%20%7B%0A%20%20%20%20%20%20%20%20%20%20%20%20phoneNumber%0A%20%20%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%0A%7D%0A&variables=%7B%0A%20%20%20%20%22userId%22%3A%20%22VXNlclR5cGU6MQ%3D%3D%22%0A%7D)

<sup>*\*You may need to update the url host and port*</sub>


Updates the profile information for the user that matches the provided id, with the given input.
**Note** If there is no profile in the database, then it will be created
even though this should happen when the User was added to the system.
:return:

## Variables
```json
{
    "userId": "VXNlclR5cGU6MQ=="
}
```
## Request
```graphql

query GetPendingApprovals {

  approvalRequestPolicies {
    edges {
      node {
        name
        permission {
          name
        }
        requests {
          edges {
            node {
              profile {
                phoneNumber
                parent {
                  phoneNumber
                }
              }
            }
          }
        }
      }
    }
  }

  approvalRequests {
    edges {
      node {
        policy {
          name
          permission {
            name
            codename
            contentType {
              appLabel
              model
            }
          }
        }
        profile {
          phoneNumber
          parent {
            phoneNumber
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
        "approvalRequestPolicies": {
            "edges": [
                {
                    "node": {
                        "name": "Can approve profile changes Policy",
                        "permission": {
                            "name": "Can approve profile changes"
                        },
                        "requests": {
                            "edges": [
                                {
                                    "node": {
                                        "profile": {
                                            "phoneNumber": "+12125552368",
                                            "parent": {
                                                "phoneNumber": "+12125552368"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        },
        "approvalRequests": {
            "edges": [
                {
                    "node": {
                        "policy": {
                            "name": "Can approve profile changes Policy",
                            "permission": {
                                "name": "Can approve profile changes",
                                "codename": "approve_profile_changes",
                                "contentType": {
                                    "appLabel": "core",
                                    "model": "profile"
                                }
                            }
                        },
                        "profile": {
                            "phoneNumber": "+12125552368",
                            "parent": {
                                "phoneNumber": "+12125552368"
                            }
                        }
                    }
                }
            ]
        }
    }
}
```
