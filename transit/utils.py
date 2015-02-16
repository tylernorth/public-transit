from bs4 import BeautifulSoup
import requests

from transit.exceptions import TransitException

def make_request(url):
    '''Check return 200 and not error'''
    headers = {'accept-encoding' : 'gzip, deflate'}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        raise TransitException("URL:%s does not return 200" % url)

    soup = BeautifulSoup(r.text)
    error = soup.find('error')
    if error:
        raise TransitException("URL:%s returned error:%s" % (url, error.string))

    return soup
