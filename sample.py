# Sample file to demonstrate how to use UMUTextStats from an API
import requests
import json
import tempfile
import pandas as pd
import numpy as np

# @var sample_text String 
sample_text = 'Vamos a probar con un texto un poco más largo'


# @var umutextstats_endpoint String The end point
umutextstats_endpoint = 'https://umuteam.inf.um.es/umutextstats/api/'


# First step. Login at the system
# @todo. Put your credentials
# @var login_request_data Object
login_request_data = {
    'email': '',
    'password': ''
}


# Make login request
r = requests.post (umutextstats_endpoint + 'login', json = login_request_data, verify = False)
if 200 != r.status_code:
    raise ValueError ('Login failed')


# Store the authentication token
auth_token = r.json ()['data']['token']


# @var text_request_data Object
text_request_data = {
    'source-provider': 'text',
    'content': sample_text,
    'format': 'csv',
    'model': 'umutextstats',
    'umutextstats-config': 'default.xml'
}


# Do request
r = requests.post (
    umutextstats_endpoint + 'stats.csv', 
    json = text_request_data, 
    verify = False, 
    headers = {
        'Authorization': auth_token,
        'Content-type': 'text/html; charset=UTF-8'
    }
)

if 200 != r.status_code:
    raise ValueError ('Request failed')


# Get the file
# We strip the response, as we return some extra bytes to the progress bar
response = json.loads (r.text[r.text.find ('{'):])
file = response['file']

r = requests.get (
    umutextstats_endpoint + file,
    verify = False, 
    headers = {
        'Authorization': auth_token
    }
)


# Get the response
data = r.text


# Extract the values
rows = [x.split (',') for x in data.split ('\n')[1:-1]]


# Get columns to build a dataframe
columns = [x for x in data.split ('\n')[0].split (',')][:-1]


# Get final dataframe
features = [row[:-1] for row in rows]
features = list (np.float_ (features))
features = pd.DataFrame (features, columns = columns)


# Here you can store the results in a CSV or combine several dataframes
print (features)
