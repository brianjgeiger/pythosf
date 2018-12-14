from .api_detail import APIDetail


class User(APIDetail):
    def __init__(self, session, id=None, self_link=None, data=None):
        super().__init__(session=session, data=data)
        if not data:
            self.id = id
            self.type = 'users'
            self.links = None
            self.meta = None
            self.self_link = self_link

    def get(self, query_parameters=None, auth=None):
        url = '/v2/users/me/'
        if self.self_link:
            url = self.self_link
        elif self.links:
            url = self.links.self
        elif self.id:
            url = '/v2/users/{}/'.format(self.id)

        response = self.session.get(
            url=url, query_parameters=query_parameters, auth=auth)
        if response:
            self._update(response=response)
        else:
            raise ValueError(
                "No url or id to get. Set the id or self_link then try to get.")
