import json
import urllib
import requests
import time
from .utils import combine_headers, save_attribute_items, unwrap_data
from . import exceptions


class Session:
    def __init__(self, api_base_url, token, default_version=None):
        self.api_base_url = api_base_url
        self.default_version = default_version
        self.token = token

    def base_headers(self):
        return {
            'content-type': 'application/vnd.api+json',
            'Authorization': 'Bearer {}'.format(self.token),
        }

    def json_api_request(self, url, method=None, item_id=None, item_type=None, attributes=None, raw_body=None,
                         query_parameters=None, fields=None, headers=None, retry=True):
        request_body = {}

        url = urllib.parse.urljoin(base=self.api_base_url, url=url)
        request_data = {}

        if raw_body is None:
            if attributes is not None:
                request_body['attributes'] = attributes
            if item_id is not None:
                request_body['id'] = id
            if item_type is not None:
                request_body['type'] = item_type
            if request_body is not None:
                request_data['data']=request_body

        if method is not None:
            method = method.upper()
        if query_parameters:
            if not query_parameters.get('version', None):
                query_parameters.update({'version': self.default_version})
        else:
            query_parameters = {'version': self.default_version}
        keep_trying = True
        response = None

        while keep_trying:
            keep_trying = False
            try:
                if method == 'GET':
                    response = requests.get(url, params=query_parameters,
                                            headers=combine_headers(self.base_headers(), headers))
                elif method == 'POST':
                    response = requests.post(url, params=query_parameters, json=request_data, data=raw_body,
                                             headers=combine_headers(self.base_headers(), headers))
                elif method == 'PUT':
                    response = requests.put(url, params=query_parameters, json=request_data, data=raw_body,
                                            headers=combine_headers(self.base_headers(), headers))
                elif method == 'PATCH':
                    response = requests.patch(url, params=query_parameters, json=request_data, data=raw_body,
                                              headers=combine_headers(self.base_headers(), headers))
                elif method == 'DELETE':
                    response = requests.delete(url, params=query_parameters,
                                               headers=combine_headers(self.base_headers(), headers))
                else:
                    raise exceptions.UnsupportedHTTPMethod("Only GET/POST/PUT/PATCH/DELETE supported, not {}".format(method))
                if response.status_code == 429:
                    keep_trying = retry
                    response_headers = response.headers
                    wait_time = response_headers['Retry-After']
                    if keep_trying:
                        print("Throttled: retrying in {wait_time}s")
                        time.sleep(int(wait_time))
                    else:
                        print("Throttled. Please retry after {wait_time}s")
                elif response.status_code >= 400:
                    status_code = response.status_code
                    content = getattr(response, 'content', None)
                    raise requests.exceptions.HTTPError("Status code {}. {}".format(status_code, content))
            except requests.exceptions.RequestException as e:
                print('HTTP Request failed: {}'.format(e))
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            return None

    def get(self, url, query_parameters=None, headers=None, retry=True):
        return self.json_api_request(url=url, method="GET", query_parameters=query_parameters,
                                     headers=headers, retry=retry)

    def post(self, url, item_type, query_parameters=None, attributes=None, headers=None, retry=True):
        return self.json_api_request(url=url, method="POST", item_type=item_type, attributes=attributes,
                                     query_parameters=query_parameters,
                                     headers=headers, retry=retry)

    def put(self, url, item_id, item_type, query_parameters=None, attributes=None, headers=None,
            retry=True):
        return self.json_api_request(url=url, method="PUT", item_id=item_id, item_type=item_type, attributes=attributes,
                                     query_parameters=query_parameters, headers=headers, retry=retry)

    def patch(self, url, item_id, item_type, query_parameters=None, attributes=None, headers=None,
              retry=True):
        return self.json_api_request(url=url, method="PATCH", item_id=item_id, item_type=item_type, attributes=attributes,
                                     query_parameters=query_parameters, headers=headers, retry=retry)

    def delete(self, url, item_type, query_parameters=None, attributes=None, headers=None,
               retry=True):
        self.json_api_request(url=url, method="DELETE", item_type=item_type, attributes=attributes,
                                     query_parameters=query_parameters, headers=headers, retry=retry)
        return None

    @staticmethod
    def remove_none_items(items):
        return {key: value for key,value in items.items() if value is not None and key != 'self'}


class TopLevelData:
    def __init__(self, response, tld_key):
        self.update(response=response, tld_key=tld_key)

    def update(self, response, tld_key):
        tld_data = unwrap_data(response)
        if tld_data:
            tld = tld_data.get(tld_key, None)
            if tld:
                save_attribute_items(self, response_attributes=tld)


class APIDetail:
    def __init__(self, session, data=None):
        self.session=session
        if data is not None:
            self._update(response=data)

    def _update(self, response):
        response_data = unwrap_data(response)

        if response_data:
            response_attributes = response_data['attributes']
            save_attribute_items(self, response_attributes=response_attributes)
            self.id = response_data.get('id', None)
            self.relationships = TopLevelData(response=response, tld_key='relationships')
            self.links = TopLevelData(response=response, tld_key='links')
            self.meta = TopLevelData(response=response, tld_key='meta')


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

    def create(self, title, category="project", description=None, public=None, tags=None, template_from=None):
        saved_args = locals()
        attributes = self.session.remove_none_items(saved_args)
        response = self.session.post(url='/v2/nodes/', item_type=self.type, attributes=attributes)
        if response:
            self._update(response=response)

    def delete(self):
        if self.id is None:
            return None
        else:
            self_url = self.links.self
            self.session.delete(url=self_url, item_type=self.type)
            self.id = None
            return None

    def get(self):
        url = None
        if self.self_link:
            url = self.self_link
        elif self.links:
            url = self.links.self
        elif self.id:
            url = '/v2/nodes/{}/'.format(self.id)

        if url:
            response = self.session.get(url=url)
            if response:
                self._update(response=response)
        else:
            raise ValueError("No url or id to get. Set the id or self_link then try to get.")

    def get_providers(self):
        if not getattr(self, 'relationships', False):
            self.get()
        providers_url = self.relationships.files['links']['related']['href']
        response = self.session.get(url=providers_url)
        if response:
            providers = response['data']
            for provider in providers:
                self.providers.append(Provider(session= self.session, data=provider))

        return self.providers


class File(APIDetail):
    def __init__(self, session, node=None, location=None, name=None, data=None):
        super().__init__(session=session, data=data)
        if data is None:
            self.name = name
            self.location = location
            self.type = "file"
            self.node = node
            self.session = session

    def get(self):
        pass

    def download(self):
        raise NotImplementedError

    def upload(self):
        raise NotImplementedError

    def move(self):
        pass

    def copy(self):
        pass

    def delete(self):
        pass

    def rename(self):
        pass


class Folder(File):
    def __init__(self, session, node=None, location=None, name=None, data=None):
        super().__init__(session=session, node=node, location=location, name=name, data=data)
        self.type = "files"

    def download(self):
        raise exceptions.UnsupportedMethod("Cannot download a folder")

    def list(self):
        return self.get()

    def create(self):
        pass

    def delete(self):
        pass

    def move(self):
        pass

    def copy(self):
        pass

    def rename(self):
        pass

    def upload(self):
        pass


class Provider(Folder):
    pass


