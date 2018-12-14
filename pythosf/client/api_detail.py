from ..utils import save_attribute_items, unwrap_data


class APIDetail:
    def __init__(self, session, data=None, wb_data=None):
        self.session = session
        if data is not None:
            self._update(response=data)

    def _update(self, response):
        response_data = unwrap_data(response)

        if response_data:
            if 'attributes' in response_data:
                response_attributes = response_data['attributes']
            else:
                response_attributes = response_data
            save_attribute_items(self, response_attributes=response_attributes)
            self.id = response_data.get('id', None)
            self.relationships = TopLevelData(
                response=response, tld_key='relationships')
            self.links = TopLevelData(response=response, tld_key='links')
            self.meta = TopLevelData(response=response, tld_key='meta')


class TopLevelData:
    def __init__(self, response, tld_key):
        self.update(response=response, tld_key=tld_key)

    def update(self, response, tld_key):
        tld_data = unwrap_data(response)
        if tld_data:
            tld = tld_data.get(tld_key, None)
            if tld:
                save_attribute_items(self, response_attributes=tld)

