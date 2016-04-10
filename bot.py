# -*- coding:utf-8 -*-

import os
import json
import urllib.parse
from html.parser import HTMLParser

import requests
import flask

# from config import CID, CS, MID
CID = os.environ.get('CID')
CS = os.environ.get('CS')
MID = os.environ.get('MID')
PROXY = os.environ.get('PROXY')

app = flask.Flask(__name__)


def check(_from, _to):
    class LastTrainParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.found = False
            self.result = []

        def handle_starttag(self, tag, attrs):
            if dict(attrs).get('id') == 'Bk_list_tbody':
                self.found = True

        def handle_endtag(self, tag):
            if self.found and tag == 'tr':
                self.found = False

        def handle_data(self, data):
            if self.found and data != '\n':
                self.result.append(data)

    encode = urllib.parse.quote
    url = 'http://www.jorudan.co.jp/norikae/cgi/nori.cgi?rf=top&eok1=&eok2=R-&pg=0&eki1={}&Cmap1=&eki2={}&Dym=201604&Ddd=9&Dhh=7&Dmn1=4&Dmn2=4&Cway=3&Cfp=1&Czu=2&S.x=101&S.y=19&S=%E6%A4%9C%E7%B4%A2&Csg=1'.format(encode(_from), encode(_to))
    response = requests.get(url)
    parser = LastTrainParser()
    parser.feed(response.text)
    parser.result.insert(0, '→'.join([_from, _to]) + ' 最終電車')
    return '\n'.join(parser.result)


def receive():
    data = json.loads(flask.request.data.decode('utf-8'))
    result = data['result'][0]
    return result['from'], result['content']['text'].split('から')


def reply(user, result):
    url = 'https://trialbot-api.line.me/v1/events'
    headers = {
        'Content-Type': 'application/json; charser=UTF-8',
        'X-Line-ChannelID': CID,
        'X-Line-ChannelSecret': CS,
        'X-Line-Trusted-User-With-ACL': MID
    }
    values = {
        'to': user,
        'toChannel': 1383378250,  # Fixed value
        'eventType': "138311608800106203",  # Fixed value
        'content': result,
    }
    proxies = {'http': PROXY, 'https': PROXY}
    data = urllib.parse.urlencode(values).encode('utf-8')
    requests.post(url, data=data, headers=headers, proxies=proxies)


@app.route('/', methods=['POST'])
def main():
    user, (_from, _to) = receive()
    reply(user, check(_from, _to))
    return 'Done'

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5000)))
