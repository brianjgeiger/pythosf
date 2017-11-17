# pythosf
A quick python api client for the Open Science Framework. (You're probably better off using [osf-client](https://github.com/osfclient/osfclient) instead.)

Example usage:

```py
    from pythosf import client

    test_session = client.Session(api_base_url="https://staging-api.osf.io/", token=STAGING_TOKEN)

    new_node = client.Node(session=test_session)
    new_node.create(title="Quick test 4")
    print(getattr(new_node, 'title', None))
    print(getattr(new_node, 'date_modified', None))
    new_node.delete()

    some_project = client.Node(session=test_session, id='9h53q')
    some_project.get_providers()
    print(getattr(some_project, 'title', None))
```
