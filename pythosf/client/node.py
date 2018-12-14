from .api_detail import APIDetail


class Node(APIDetail):
    def __init__(self, session, id=None, self_link=None, data=None):
        super().__init__(session=session, data=data)
        if not data:
            self.id = id
            self.type = 'nodes'
            self.links = None
            self.meta = None
            self.self_link = self_link
        self.providers = []

    def create(self, title, category="project", description=None, public=None, tags=None,
               template_from=None, query_parameters=None, auth=None):
        saved_args = locals()
        attributes = self.session.remove_none_items(saved_args)
        response = self.session.post(url='/v2/nodes/', item_type=self.type, attributes=attributes,
                                     query_parameters=query_parameters, auth=auth)
        if response:
            self._update(response=response)
        return self

    def create_child(self, title, category="project", description=None, public=None, tags=None,
                     template_from=None, query_parameters=None, auth=None):
        saved_args = locals()
        attributes = self.session.remove_none_items(saved_args)
        child_node = Node(session=self.session)
        url = self.relationships.children['links']['related']['href']
        response = self.session.post(url=url, item_type=self.type, attributes=attributes,
                                     query_parameters=query_parameters, auth=auth)
        if response:
            child_node._update(response=response)
        return child_node

    def delete(self, query_parameters=None, auth=None):
        if self.id is None:
            return None
        else:
            self_url = self.links.self
            self.session.delete(url=self_url, item_type=self.type,
                                query_parameters=query_parameters, auth=auth)
            self.id = None
            return None

    def get(self, query_parameters=None, auth=None):
        url = None
        if self.self_link:
            url = self.self_link
        elif self.links:
            url = self.links.self
        elif self.id:
            url = '/v2/nodes/{}/'.format(self.id)

        if url:
            response = self.session.get(
                url=url, query_parameters=query_parameters, auth=auth)
            if response:
                self._update(response=response)
        else:
            raise ValueError(
                "No url or id to get. Set the id or self_link then try to get.")

    def get_providers(self, query_parameters=None, auth=None):
        if not getattr(self, 'relationships', False):
            self.get(auth=auth)
        providers_url = self.relationships.files['links']['related']['href']
        response = self.session.get(
            url=providers_url, query_parameters=query_parameters, auth=auth)
        if response:
            providers = response['data']
            for provider in providers:
                self.providers.append(
                    Provider(session=self.session, data=provider))

        return self.providers
