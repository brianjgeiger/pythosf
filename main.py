import json
import urllib
import requests
import time

TEMPLATE_BASE_NAME = 'ABC Template'
TEMPLATE_LOCATION = 'ABC Templates'
FOLDER_BASE_NAME = 'ABC'

RAW_DATA_NODE_ID = 'tjvx6'
DATA_ENTRY_NODE_ID = 'rkxcb'

RAW_DATA_NODE_PROVIDER = 'googledrive'
DATA_ENTRY_NODE_PROVIDER = 'googledrive'


API_BASE_URL = 'https://api.osf.io/'
DEFAULT_API_VERSION = '2.6'


def combine_headers(header_one, header_two):
    if header_two is None:
        return header_one
    elif header_one is None:
        return header_two
    else:
        return {**header_one, **header_two}

# ------------------- PyCharm specific code


def api_token():
    """
    Never store the api_token in a variable in a Jupyter notebook. Always call this function to get the token.
    """
    return 'notarealtoken'


# -------------------- Models


class MisorderedDates(Exception):
    pass


class NotAHalf(Exception):
    pass


class WrongNumberOfParts(Exception):
    pass


class OnlyOneName(Exception):
    pass


class UnsupportedHTTPMethod(Exception):
    pass


class APITimeoutWithoutRetry(Exception):
    pass


class UnsupportedMethod(Exception):
    pass


class Template:
    def __init__(self, name, location, base_name):
        self.name = name
        self.location = location
        self.base_name = base_name
        self.start_year = None
        self.start_year_half = 1
        self.end_year = None
        self.end_year_half = 2
        self.decompose_name()

    def decompose_name(self):
        base_name_end = len(self.base_name) + 1
        splittable_string = self.name[base_name_end:].strip()
        removed_extension = splittable_string.split('.')[0]
        split_string = removed_extension.split('-')
        split_length = len(split_string)
        if split_length == 2:
            self.start_year = int(split_string[0])
            self.end_year = int(split_string[1])
        elif split_length == 3:
            self.start_year = int(split_string[0])
            second_part = int(split_string[1])
            third_part = int(split_string[2])
            self.end_year = max(second_part, third_part)
            if second_part > third_part:
                self.end_year_half = third_part
            else:
                self.start_year_half = second_part
        elif split_length == 4:
            self.start_year = int(split_string[0])
            self.start_year_half = int(split_string[1])
            self.end_year = int(split_string[2])
            self.end_year_half = int(split_string[3])
        else:
            raise WrongNumberOfParts("Expected 2, 3, or 4 parts of date range. Got {split_length} on {self.base_name}")

        if self.start_year > self.end_year:
            raise MisorderedDates('Start year {self.start_year} is after end year {self.end_year} on {self.base_name}')
        if self.start_year == self.end_year and self.start_year_half >= self.end_year_half:
            raise MisorderedDates('Year halfs are equal or out of order on {self.base_name}')
        if self.start_year_half != 1 and self.start_year_half != 2:
            raise NotAHalf('Start year half needs to be 1 or 2. Was {self.start_year_half} on {self.base_name}')
        if self.end_year_half != 1 and self.end_year_half != 2:
            raise NotAHalf('End year half needs to be 1 or 2. Was {self.end_year_half} on {self.base_name}')

    @staticmethod
    def start_end(year, half):
        if year:
            if half == 1:
                return year + .1
            if half == 2:
                return year + .9
        return None

    @property
    def start(self):
        return self.start_end(self.start_year, self.start_year_half)

    @property
    def end(self):
        return self.start_end(self.end_year, self.end_year_half)


# --------------------- API

class Session:
    def __init__(self, api_base_url, default_version=None):
        self.api_base_url = api_base_url
        self.default_version = default_version or DEFAULT_API_VERSION

    @staticmethod
    def token():
        # If this weren't a Jupyter Notebook, this would just be replaced with a property
        return api_token()

    @staticmethod
    def base_headers():
        return {
            'content-type': 'application/vnd.api+json',
            'Authorization': 'Bearer {}'.format(api_token()),
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
                query_parameters.update({'version': DEFAULT_API_VERSION})
        else:
            query_parameters = {'version': DEFAULT_API_VERSION}
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
                    raise UnsupportedHTTPMethod("Only GET/POST/PUT/PATCH/DELETE supported, not {}".format(method))
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


def save_attribute_items(target, response_attributes):
    for key,value in response_attributes.items():
        setattr(target, key, value)


class TopLevelData:
    def __init__(self, response, tld_key):
        self.update(response=response, tld_key=tld_key)

    def update(self, response, tld_key):
        tld_data = response.get('data', None)
        if tld_data:
            tld = tld_data.get(tld_key, None)
            if tld:
                save_attribute_items(self, response_attributes=tld)


class Node:
    def __init__(self, session, id=None, self_link=None):
        super().__init__()
        self.id = id
        self.session = session
        self.type = 'nodes'
        self.links = None
        self.meta = None
        self.self_link = self_link
        self.providers = []

    def _update(self, response):
        response_data = response.get('data', None)
        if response_data:
            response_attributes = response_data['attributes']
            save_attribute_items(self, response_attributes=response_attributes)
            self.id = response_data.get('id', None)
            self.relationships = TopLevelData(response=response, tld_key='relationships')
            self.links = TopLevelData(response=response, tld_key='links')
            self.meta = TopLevelData(response=response, tld_key='meta')

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
            pass


class File:
    def __init__(self, node, session, location, name=None):
        super().__init__()
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
    def __init__(self, node, session, location, name=None):
        super().__init__(node, session, location, name=None)
        self.type = "files"

    def get(self):
        pass

    def download(self):
        raise UnsupportedMethod("Cannot download a folder")

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
        def __init__(self, node, session, provider_name, name=None):
            super().__init__(node=node, session=session, location=provider_name, name=name)
            self.provider_name = provider_name


# -------------------- manual api test


def main():
    test_session = Session(api_base_url="https://staging-api.osf.io/")

    # new_node = Node(session=test_session)
    # new_node.create(title="Quick test 4")
    # print(getattr(new_node, 'title', None))
    # print(getattr(new_node, 'date_modified', None))
    # new_node = new_node.delete()
    some_project = Node(session=test_session, id='9h53q')
    some_project.get_providers()
    print(getattr(some_project, 'title', None))



main()