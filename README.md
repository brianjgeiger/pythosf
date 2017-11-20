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
    providers = some_project.get_providers()
    print(getattr(some_project, 'title', None))

    my_provider = None
    for provider in providers:
        if provider.name == TEST_NODE_PROVIDER:
            my_provider = provider
            break
    my_provider.get(retrieve_all=True) 
    files = my_provider.files
    for file in files:
        if file.name == '1.png':
            my_file = file
        elif file.name == 'ten':
            my_folder = file
    my_file.move(to_folder=my_folder, conflict='replace')
```
