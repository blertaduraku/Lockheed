import sys
import requests
from utils import *


def authenticate():
    # read config from file
    config = read_config()

    # read credentials info from config
    email = config['login']['user']
    password = config['login']['passwd']
    workspace = config['login']['workspaceId']
    base_url = config['host']
    login_url = base_url + "/p/login"

    # prepare headers for the login request
    headers = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    # prepare data form for the login request
    data = {
        'tokenonly': 'true',
        'name': email,
        'password': password,
        'tenant': workspace
    }

    # initiate a session and post the login request
    login_request = requests.Session()
    response = login_request.post(login_url, data=data, headers=headers)

    # check the login request is successful, the response text should a token of 32 characters
    if len(response.text) > 32:
        print('Login failed. Please check Login info in Config.yaml file.')
        sys.exit()

    else:
        # get the cookies from the login response
        # fixed cookies
        auth_cookies = {
            'JSESSIONID': response.cookies['JSESSIONID'],
            'identifier': response.cookies['identifier'],
            'login': response.cookies['login']
        }
        # optional cookies depending on host location
        for cookie_section in 'AWSELB', 'LBROUTEID':
            if cookie_section in response.cookies:
                auth_cookies[cookie_section] = response.cookies[cookie_section]

        # prepare the header for next authorised requests, to contain the login token
        auth_headers = {
            'Accept': "application/json",
            'x-signavio-id': response.text,
        }

        # initiate a session for a new authorised request with updated cookies and headers
        authorised_request = requests.Session()
        authorised_request.cookies.update(auth_cookies)
        authorised_request.headers.update(auth_headers)

        # return the authorised request
        return authorised_request


# EXAMPLE #
my_auth_request = authenticate()
print('Returned Cookies : \n' + str(my_auth_request.cookies))
print('Returned Token : \n' + str(my_auth_request.headers['x-signavio-id']) + '\n\n')
