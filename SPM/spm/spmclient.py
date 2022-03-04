import urllib.parse

import requests
import yaml
import json
import html


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SPMClient(metaclass=Singleton):

    def __init__(self, config_file_path):

        with open(config_file_path) as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        self.host = config['host']

        req = requests.Session()

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            'tokenonly': True,
            'name': config['mail'],
            'password': config['password'],
            'tenant': config['workspace']
        }

        url = self.host + "/p/login"

        response = req.post(url, data=data, headers=headers)

        # Response contains the basic HTML code in case if login failure. Otherwise a 32-character string
        if len(response.text) > 50:
            print('Login failed.')
            return

        else:

            print('Login successful.')
            server = ''
            server_region = ''

            for cookie_section in 'AWSELB', 'LBROUTEID':
                if cookie_section in response.cookies:
                    server_region = cookie_section
                    server = response.cookies[cookie_section]

            auth_cookies = {
                'JSESSIONID': response.cookies['JSESSIONID'],
                'identifier': response.cookies['identifier'],
                'login': response.cookies['login'],
                'token': response.text,
                server_region: server
            }

        self.auth_req = requests.Session()

        auth_headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': "application/json",
            'x-signavio-id': response.text
        }

        self.auth_req.cookies.update(auth_cookies)
        self.auth_req.headers.update(auth_headers)

    def _request_JSON(self, method, url, data={}):

        try:

            if method == 'GET':
                return self.auth_req.get(url, data=data).json()

            elif method == 'POST':
                return self.auth_req.post(url, data=data).json()

            elif method == 'PUT':
                return self.auth_req.put(url, data=data).json()

        except Exception as err:
            print(err.with_traceback())

    '''

    Directory Methods

    '''

    def get_root_folder_content(self):

        url = self.host + '/p/directory'

        return self._request_JSON('GET', url)

    def get_folder_content(self, directory_id):

        if '/directory/' in directory_id:
            url = self.host + '/p' + directory_id
        else:
            url = self.host + '/p/directory/' + directory_id

        return self._request_JSON('GET', url)

    def get_folder_info(self, directory_id):

        if '/directory/' in directory_id:
            url = self.host + '/p' + directory_id + '/info'
        else:
            url = self.host + '/p/directory/' + directory_id + '/info'

        return self._request_JSON('GET', url)

    def directory_create(self, name, parent, desc=''):

        url = self.host + '/p/directory'

        if '/directory/' not in parent:
            parent = '/directory/' + parent

        body = {
            'name': html.unescape(name),
            'description': desc,
            'parent': parent
        }

        return self._request_JSON('POST', url, body)

    '''

    Meta Methods

    '''

    def get_meta(self):

        url = self.host + '/p/meta'

        return self._request_JSON('GET', url)

    '''

    Model Methods

    '''

    def head_revision_get_editor_data(self, model_id):

        if '/model/' in model_id:
            url = self.host + '/p/editordata?id=' + model_id.replace('/model/', '')
        else:
            url = self.host + '/p/editordata?id=' + model_id

        return self._request_JSON('GET', url)

    def get_diagram_json(self, model_id):

        if '/model/' in model_id:
            url = self.host + '/p' + model_id + '/json'
        else:
            url = self.host + '/p/model/' + model_id + '/json'

        return self._request_JSON('GET', url)

    def get_diagram_header(self, model_id):

        if '/model/' in model_id:
            url = self.host + '/p' + model_id + '/info'
        else:
            url = self.host + '/p/model/' + model_id + '/info'

        return self._request_JSON('GET', url)

    def get_diagram_notification(self, model_id):

        if '/model/' in model_id:
            url = self.host + '/p' + model_id + '/notification'
        else:
            url = self.host + '/p/model/' + model_id + '/notification'

        return self._request_JSON('GET', url)

    def update_model(self, model_id, model_json, comment='Automatic Python Update', new_name=None):

        if not '/model/' in model_id:
            model_id = '/model/' + model_id

        url = self.host + '/p' + model_id

        model_header = self.get_diagram_header(model_id)

        body = {
            'name': model_header['name'] if not new_name else new_name,
            'parent': model_header['parent'],
            'description': model_header['description'],
            'comment': comment if comment else model_header['comment'],
            'json_xml': json.dumps(model_json)
        }

        return self._request_JSON('PUT', url, body)

    def publish_model(self, model_id):

        url = self.host + '/p/publish'

        if '/model/' in model_id:
            pass
        else:
            model_id = '/model/' + model_id

        body = {
            'models': model_id,
            'mode': 'publish'
        }

        return self._request_JSON('POST', url, body)

    def diagram_create(self, name, parent, json_data, namespace='http://b3mn.org/stencilset/bpmn2.0#'):

        url = self.host + '/p/model'

        body = {
            'name': html.unescape(name),
            'parent': parent,
            'json_xml': json.dumps(json_data),
            'namespace': namespace
        }

        return self._request_JSON('POST', url, body)

        return

    '''

    Syntax Checking Methods

    '''

    def check_model_syntax(self, model_id, model_json, guideline_id):

        url = self.host + '/p/mgeditorchecker'

        if '/model/' in model_id:
            model_id = model_id.split('/model/')[1]

        body = {
            'id': model_id,
            'guideline_id': guideline_id,
            'model_json': json.dumps(model_json),
            'comments': json.dumps({})
        }

        return self._request_JSON('POST', url, body)

    '''

    Dictionary Methods

    '''

    def get_all_dictionary_categories(self, optional_id=''):

        if '/glossarycategory/' in optional_id:
            optional_id = optional_id.split('/glossarycategory/')[1]

        url = self.host + '/p/glossarycategory/' + optional_id

        return self._request_JSON('GET', url)

    def get_all_entries_of_category(self, category_id, limit=None, offset=None):

        if '/glossarycategory/' in category_id:
            url = self.host + '/p/glossary?category=' + category_id.split('/glossarycategory/')[1]
        else:
            url = self.host + '/p/glossary?category=' + category_id

        if limit is not None:
            url = url + '&limit=' + str(limit)
        if offset is not None:
            url = url + '&offset=' + str(offset)

        url = url + '&sort=title'

        return self._request_JSON('GET', url)

    def get_dictionary_entry_rel_info(self, entry_id):

        if '/glossary/' in entry_id:
            url = self.host + '/p' + entry_id + '/info/'
        else:
            url = self.host + '/p/glossary/' + entry_id + '/info/'

        return self._request_JSON('GET', url)

    def get_dictionary_entry_rel_link(self, entry_id):

        if '/glossary/' in entry_id:
            url = self.host + '/p' + entry_id + '/link/'
        else:
            url = self.host + '/p/glossary/' + entry_id + '/link/'

        return self._request_JSON('GET', url)

    def create_new_entry(self, data):

        url = self.host + '/p/glossary/'

        return self._request_JSON('POST', url=url, data=data)

    def update_dictionary_entry(self, entry_id, data):

        if not '/glossary/' in entry_id:
            entry_id = '/glossary/' + entry_id

        url = self.host + '/p' + entry_id + '/info'

        return self._request_JSON('PUT', url, data)

    '''

    Utility Methods

    '''

    def map_attribute_meta(self, meta_name):

        for entry in self.meta:

            if entry['href'].split('/meta/')[1] == meta_name:
                return entry

    def get_all_sub_directories(self, dir, directories=[]):

        directory = self.get_folder_content(dir)

        for item in directory:

            if item['rel'] == 'dir':
                directories.append(item)
                self.get_all_sub_directories(item['href'], directories)

        return directories

    def get_directories_models(self, dir, model_filter=[], recursive=True, models=[], excluded_directories=[], index=0):

        if dir not in excluded_directories:
            print('> SEARCHING DIRECTORY ID', dir)

            directory = self.get_folder_content(dir)

            for item in directory:

                if item['rel'] == 'mod':
                    item['level'] = index

                    if model_filter:

                        if item['rep']['namespace'] in model_filter:
                            models.append(item)
                    else:
                        models.append(item)

                if recursive:
                    if item['rel'] == 'dir':
                        self.get_directories_models(item['href'], model_filter, True, models, excluded_directories, index + 1)

        return models

    '''

    Search Methods

    '''

    def search_spm(self, params):

        qs = urllib.parse.urlencode(params)
        url = self.host + '/p/search?' + qs

        return self._request_JSON('GET', url)
