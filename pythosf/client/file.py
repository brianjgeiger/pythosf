import json
from .api_detail import APIDetail


class File(APIDetail):
    def __init__(self, session, node=None, location=None, name=None, data=None, wb_data=None, auth=None):
        super().__init__(session=session, data=data)
        if wb_data is not None:
            self._update_from_wb(wb_data=wb_data, auth=auth)
        elif data is None:
            self.name = name
            self.location = location
            self.type = "file"
            self.node = node
            self.session = session

    def _update_from_wb(self, wb_data, auth=None):
        auth = auth or self.session.auth
        wb_attributes = wb_data['data']['attributes']
        if wb_attributes['provider'] == 'osfstorage':
            osf_url = "{}v2/files{}".format(self.session.api_base_url,
                                            wb_attributes['path'])
        else:
            osf_url = "{}v2/nodes/{}/files/{}{}?info".format(
                self.session.api_base_url,
                wb_attributes['resource'],
                wb_attributes['provider'],
                wb_attributes['path']
            )
        response = self.session.get(url=osf_url, auth=auth)
        self._update(response=response)

    def get(self, url=None, query_parameters=None, auth=None):
        if url:
            self.location = url
        elif self.links.self:
            self.location = self.links.self
        # todo elif node, location, and name

        response = self.session.get(
            url=self.location, query_parameters=query_parameters, auth=auth)
        self._update(response=response)

    def download(self, query_parameters=None, auth=None):
        url = self.links.download
        return self.session.get(url=url, query_parameters=query_parameters, auth=auth)

    def upload(self, data, query_parameters=None, auth=None):
        url = self.links.upload
        query_parameters = query_parameters or {}
        upload_query_parameters = {
            'kind': 'file',
        }
        combined_query_parameters = {
            **query_parameters, **upload_query_parameters}
        return self.session.put(url=url, query_parameters=combined_query_parameters, raw_body=data, auth=auth)

    def _move_or_copy(self, to_folder, action, rename=None, conflict=None, query_parameters=None, auth=None):
        body = {
            'action': action,
            'path': to_folder.path,
            'resource': to_folder.relationships.node['data']['id'],
            'provider': to_folder.provider,
        }
        if rename:
            body['rename'] = rename
        if conflict:
            body['conflict'] = conflict
        raw_body = json.JSONEncoder().encode(body)
        url = self.links.move
        return self.session.post(url=url, raw_body=raw_body, query_parameters=query_parameters, auth=auth)

    def move(self, to_folder, rename=None, conflict=None, query_parameters=None, auth=None):
        moved_file = self._move_or_copy(to_folder=to_folder, action='move', rename=rename, conflict=conflict,
                                        query_parameters=query_parameters, auth=auth)
        self._update_from_wb(wb_data=moved_file, auth=auth)

    def copy(self, to_folder, rename=None, conflict=None, query_parameters=None, auth=None):
        new_file = self._move_or_copy(to_folder=to_folder, action='copy', rename=rename, conflict=conflict,
                                      query_parameters=query_parameters, auth=auth)
        return File(session=self.session, wb_data=new_file, auth=auth)

    def delete(self, query_parameters=None, auth=None):
        url = self.links.delete
        return self.session.delete(url=url, item_type=self.type, query_parameters=query_parameters, auth=auth)

    def rename(self, name, query_parameters=None, auth=None):
        body = {
            'action': 'rename',
            'rename': name
        }
        raw_body = json.JSONEncoder().encode(body)
        url = self.links.move
        response = self.session.post(
            url=url, raw_body=raw_body, query_parameters=query_parameters, auth=auth)
        self._update(response=response)
