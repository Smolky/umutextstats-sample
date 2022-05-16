# Sample file to demonstrate how to use UMUTextStats from an API
import requests
import json
import tempfile
import pandas as pd
import numpy as np
import base64
import stanza
import sys


# @var language String The language use in Stanza
language = 'es'


# @var text_label String Replace this with the field used as text in the CSV
text_label = 'tweet'


# Download Stanza model
stanza.download (language)


# @var processors String
processors = 'tokenize,mwt,pos,ner'


# @var nlp Stanza Pipeline
nlp = stanza.Pipeline (lang = language, processors = processors)



# @var tagged_pos List
tagged_pos = []


# @var tagged_ner List
tagged_ner = []


# @var f_pos lambda
f_pos = lambda x: x['text'] + '__(' + (x['xpos'] if 'xpos' in x else x['upos']) + ")" + (('(' + x['feats'] + ')') if 'feats' in x else '') if isinstance (x['id'], int) else ''


# @var f_ner lambda
f_ner = lambda x: x['type'] + '(' + x['text'] + ')'


def get_pos_and_ner (document):

    # @var sentences
    sentences = nlp (document).sentences
    
    
    # For each sentence we get its token. 
    # In order to avoid using extra memory, all operations are within comprension list
    # (1) check if document if a valid string
    # (2) use NLP to get its sentences, words, and tokens
    # (3) Apply lambda for each word to extract the information we need
    # (4) Join all sentences with a "." sign
    # POS
    tagged_pos.append (', '.join ([', '.join ([f_pos (word.to_dict ()) for word in sent.words]) for sent in sentences]))
    tagged_ner.append (', '.join ([', '.join ([f_ner (ent.to_dict ()) for ent in sent.ents]) for sent in sentences]))


# @var df DataFrame
df = pd.read_csv ('sample.csv')


# Preprocess NER and PoS
if not 'tagged_pos' in df.columns:

    # Extract the PoS and NER
    df[text_label].astype ('str').apply (lambda document: get_pos_and_ner (document) if document else ['', ''])


    # Attach response
    df.loc[:, 'tagged_pos'] = tagged_pos
    df.loc[:, 'tagged_ner'] = tagged_ner
    df.to_csv ('sample.csv', index = False)


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


# @var multipart_form_data Object
multipart_form_data = {
    'files[]': ('sample.csv', open ('sample.csv', 'r')),
}


r = requests.post (
    umutextstats_endpoint + 'file_manager/file_upload', 
    files = multipart_form_data, 
    verify = False, 
    headers = {
        'Authorization': auth_token
    }
)

if 200 != r.status_code:
    print (r.reason)
    print (r.text)
    raise ValueError ('Request failed')


# Get the file
# We strip the response, as we return some extra bytes to the progress bar
file = r.json ()['files'][0]


# @var text_request_data Object
text_request_data = {
    'source-provider': 'files',
    'file': file,
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
features.to_csv ('output.csv', index = False)


# Delete files from the UMUTextStats server
# @var delete_request_data Dict
delete_request_data = {
    'files[]': 'sample.csv'
}


# Do request
r = requests.post (
    umutextstats_endpoint + 'file_manager/delete_files', 
    json = delete_request_data, 
    verify = False, 
    headers = {
        'Authorization': auth_token,
        'Content-type': 'text/html; charset=UTF-8'
    }
)
