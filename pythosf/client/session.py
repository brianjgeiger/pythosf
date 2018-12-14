import json
import logging
import requests
import time
import urllib
from typing import List
from .. import exceptions
from ..utils import combine_headers


class Session:
    def __init__(self, api_base_url, auth=None, default_version=None, config=None):
        self.api_base_url = api_base_url
        self.default_version = default_version
        self.auth = auth
        self.request_count = 0
        self.error_count = 0

        self.base_headers = {'content-type': 'application/vnd.api+json'}

    def json_api_request(self, url, method=None, item_id=None, item_type=None, attributes=None, raw_body=None,
                         query_parameters=None, fields=None, headers=None, retry=True, auth=None):
        request_body = {}
        auth = auth or self.auth

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
                request_data['data'] = request_body
        elif raw_body == '':
            request_data = None
            raw_body = None

        if method is not None:
            method = method.upper()
        if query_parameters:
            if not query_parameters.get('version', None):
                headers=combine_headers(
                    headers,
                    {'Accept-Header': 'application/vnd.api+json;version={}'.format(self.default_version)}
                )
        else:
            headers = combine_headers(
                headers,
                {'Accept-Header': 'application/vnd.api+json;version={}'.format(self.default_version)}
            )
        keep_trying = True
        response = None

        while keep_trying:
            keep_trying = False
            try:
                if method == 'GET':
                    response = requests.get(url, params=query_parameters,
                                            headers=combine_headers(self.base_headers, headers), auth=auth)
                elif method == 'POST':
                    response = requests.post(url, params=query_parameters, json=request_data, data=raw_body,
                                             headers=combine_headers(self.base_headers, headers), auth=auth)
                elif method == 'PUT':
                    response = requests.put(url, params=query_parameters, json=request_data, data=raw_body,
                                            headers=combine_headers(self.base_headers, headers), auth=auth)
                elif method == 'PATCH':
                    response = requests.patch(url, params=query_parameters, json=request_data, data=raw_body,
                                              headers=combine_headers(self.base_headers, headers), auth=auth)
                elif method == 'DELETE':
                    response = requests.delete(url, params=query_parameters,
                                               headers=combine_headers(self.base_headers, headers), auth=auth)
                else:
                    raise exceptions.UnsupportedHTTPMethod(
                        "Only GET/POST/PUT/PATCH/DELETE supported, not {}".format(method))
                if response.status_code == 429:
                    keep_trying = retry
                    response_headers = response.headers
                    wait_time = response_headers['Retry-After']
                    if keep_trying:
                        logging.log(logging.INFO, "Throttled: retrying in {wait_time}s")
                        time.sleep(int(wait_time))
                    else:
                        logging.log(logging.ERROR, "Throttled. Please retry after {wait_time}s")
                elif response.status_code >= 400:
                    status_code = response.status_code
                    content = getattr(response, 'content', None)
                    raise requests.exceptions.HTTPError(
                        "Status code {}. {}".format(status_code, content))
                self.request_count += 1
            except requests.exceptions.RequestException as e:
                self.error_count += 1
                logging.log(logging.ERROR,'HTTP Request failed: {}'.format(e))
                raise
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            return None

    def get(self, url, query_parameters=None, headers=None, retry=True, auth=None, retrieve_all=False):
        response = self.json_api_request(url=url, method="GET", query_parameters=query_parameters,
                                         headers=headers, retry=retry, auth=auth)
        response_data = response['data']
        if retrieve_all == True and isinstance(response_data, List) and response['links']['next']:
            items = response_data
            while response['links']['next']:
                response = self.json_api_request(url=response['links']['next'], method="GET",
                                                 headers=headers, retry=retry,
                                                 auth=auth)
                response_data = response['data']
                items = items + response_data
            response['data'] = items
        return response

    def post(self, url, item_type=None, query_parameters=None, attributes=None, headers=None, retry=True, auth=None,
             raw_body=None):
        return self.json_api_request(url=url, method="POST", item_type=item_type, attributes=attributes,
                                     query_parameters=query_parameters, headers=headers, retry=retry,
                                     raw_body=raw_body, auth=auth)

    def put(self, url, item_id=None, item_type=None, query_parameters=None, attributes=None, headers=None,
            retry=True, raw_body=None, auth=None):
        return self.json_api_request(url=url, method="PUT", item_id=item_id, item_type=item_type,
                                     attributes=attributes, query_parameters=query_parameters, headers=headers,
                                     retry=retry, raw_body=raw_body, auth=auth)

    def patch(self, url, item_id, item_type, query_parameters=None, attributes=None, headers=None,
              retry=True, raw_body=None, auth=None):
        return self.json_api_request(url=url, method="PATCH", item_id=item_id, item_type=item_type,
                                     attributes=attributes, query_parameters=query_parameters, headers=headers,
                                     retry=retry, raw_body=raw_body, auth=auth)

    def delete(self, url, item_type, query_parameters=None, attributes=None, headers=None,
               retry=True, auth=None):
        self.json_api_request(url=url, method="DELETE", item_type=item_type, attributes=attributes,
                              query_parameters=query_parameters, headers=headers, retry=retry, auth=auth)
        return None

    @staticmethod
    def remove_none_items(items):
        return {key: value for key, value in items.items() if value is not None and key != 'self' and key != 'token'}
