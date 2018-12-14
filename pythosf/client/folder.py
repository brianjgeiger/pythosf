from .. import exceptions
from . import File


class Folder(File):
    def __init__(self, session, node=None, location=None, name=None, data=None, wb_data=None, auth=None):
        super().__init__(session=session, node=node, location=location, name=name, data=data,
                         wb_data=wb_data, auth=auth)
        self.type = "files"
        self.files = []

    def get(self, auth=None, append=False, query_parameters=None, retrieve_all=False):
        url = self.relationships.files['links']['related']['href']
        response = self.session.get(
            url=url, auth=auth, retrieve_all=retrieve_all, query_parameters=query_parameters)
        if response:
            files = response['data']
            if not append:
                self.files = []
            for file in files:
                file_kind = file['attributes']['kind']
                if file_kind == 'file':
                    self.files.append(File(session=self.session, data=file))
                elif file_kind == 'folder':
                    self.files.append(Folder(session=self.session, data=file))

    def download(self, query_parameters=None, auth=None):
        raise exceptions.UnsupportedMethod("Cannot download a folder")

    def list(
        self, auth=None,
        append=False,
        query_parameters=None,
        retrieve_all=False
    ):
        return self.get(
            auth=auth,
            append=append,
            query_parameters=query_parameters,
            retrieve_all=retrieve_all
        )

    def create(self, name, query_parameters=None, auth=None):
        url = self.links.new_folder
        query_parameters = query_parameters or {}
        create_query_parameters = {
            'kind': 'folder',
            'name': name,
        }
        combined_query_parameters = {
            **query_parameters, **create_query_parameters}
        new_folder_data = self.session.put(
            url=url, query_parameters=combined_query_parameters, raw_body='', auth=auth)
        return Folder(session=self.session, wb_data=new_folder_data, auth=auth)

    def upload(self, name, data, query_parameters=None, auth=None):
        url = self.links.upload
        query_parameters = query_parameters or {}
        upload_query_parameters = {
            'kind': 'file',
            'name': name,
        }
        combined_query_parameters = {
            **query_parameters, **upload_query_parameters}
        new_file_data = self.session.put(
            url=url, query_parameters=combined_query_parameters, raw_data=data, auth=auth)
        return File(session=self.session, wb_data=new_file_data)
