from datetime import date
from SPM.spm.spmclient import SPMClient
from a_authentication import authenticate
from utils import read_config

today = date.today()

spm = SPMClient(r'SPM/spmconfig.yaml')


def get_models(folder_href):
    dir_content = spm.get_folder_content(folder_href)
    for i in dir_content:
        if i['rel'] == 'dir':
            get_models(i['href'])
            # print(i['href'])
        if i['rel'] == 'mod':
            update_export_date(i['href'])


def update_export_date(href):
    model = spm.get_diagram_json(href)
    rev = spm.get_diagram_header(href)
    print(rev['rev'])
    if 'meta-exportdate' in model['properties']:
        print('EXPORT DATE', model['properties']['meta-exportdate'])


    model['properties']['meta-exportdate'] = today.strftime("%d/%m/%y")
    model['properties']['meta-revision'] = (int(rev['rev']) + 1)

    spm.update_model(href, model)


def sync_solman(href):
    config = read_config()
    base_url = config['host']
    root_folder_url = base_url + "/g/api/solman72/api/export?directory=4752203281b148c48270c93ac561b540"

    authorised_request = authenticate()
    response = authorised_request.post(root_folder_url)

    print(response.text)
    return response.text



get_models('/directory/4752203281b148c48270c93ac561b540')
sync_solman('/directory/4752203281b148c48270c93ac561b540')