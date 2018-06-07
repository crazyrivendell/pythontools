# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals


import os
import re, random
import socket
import json
import logging
from http import client
import urllib.request
import urllib.parse
from urllib.parse import urlparse, urldefrag
from html.parser import HTMLParser

log = logging.getLogger()
log.setLevel(level=logging.DEBUG)
fileLogFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
fileHandler = logging.FileHandler("log.log")
fileHandler.setFormatter(fileLogFormatter)
fileHandler.setLevel(logging.INFO)
log.addHandler(fileHandler)

consoleLogFormat = logging.Formatter(
    "%(asctime)s %(levelname)1.1s %(filename)5.5s %(lineno)3.3s-> %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(consoleLogFormat)
consoleHandler.setLevel(logging.DEBUG)
log.addHandler(consoleHandler)

Retry = 3

f = lambda x, y: x if y in x else x + [y]
# url_list = reduce(f, [[], ] + url_list)

class HtmlParser(HTMLParser):
    def __init__(self, output_list=None):
        HTMLParser.__init__(self)
        if output_list is None:
            self.output_list = []
        else:
            self.output_list = output_list

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.output_list.append(dict(attrs).get('href'))
        if tag == 'img' or tag == 'script':
            self.output_list.append(dict(attrs).get('src'))


class JsonParser:
    def __init__(self, output_list=None):
        if output_list is None:
            self.output_list = []
        else:
            self.output_list = output_list

    def feed(self, data):
        self.output_list.extend(re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", data, re.I|re.L))


class HlsPraser:
    def __init__(self, http_link):
        self.link = http_link
        self.output_list = []

    def feed(self, data):
        if data:
            for n in data.split('\n'):
                if n and n.startswith("#EXT-X-MEDIA:"):
                    uri = n.split("URI=")
                    if len(uri):
                        _uri = uri[-1]
                        self.output_list.append(urllib.parse.urljoin(self.link, _uri[1:-1].strip()))

            self.output_list.extend([urllib.parse.urljoin(self.link, m.strip()) for m in data.split('\n') if m and not m.startswith("#")])

def progress_callback(a, b, c):
    """
    :param a:  number of download blocks
    :param b:  size of a block
    :param c:  total size of the download file
    :return:
    """
    per = 100.0 * a * b / c
    if per > 100:
        per = 100
    # print('%.2f%%' % per)


class Downloader:
    def __init__(self, link, method="GET", params={}, headers={}, dst_dir="temp"):
        self.link = link
        self.retry = Retry
        self.dir = dst_dir
        self.method = method
        self.params = params
        self.headers = headers
        self.host = ""

        self.user_agents = [
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
            'Opera/9.25 (Windows NT 5.1; U; en)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
            'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
            "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 ",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0",
        ]

        socket.setdefaulttimeout(20)

        self.links = list()
        self.success = list()
        self.failure = list()
        self.id = 0

        self.links.append(self.link)

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def list_add(self, x, y):
        if y not in self.success and y not in self.failure and y not in self.links:
            x.append(y)

    def url_check(self, url):
        """
        check url and network
        :param url:
        :return:
        """
        _url = urllib.parse.urlparse(url)
        self.host = _url.netloc
        conn = client.HTTPConnection(_url.netloc)
        conn.request("HEAD", _url.path)
        if conn.getresponse():
            return True
        else:
            return False

    def parse(self):
        """
        parse request and produce download list
        :return:
        """

        default_headers = {
            "User-agent": random.choice(self.user_agents),
            "Host": self.host
        }

        link = self.links.pop(0)
        url = urlparse(link)

        # set headers&request
        self.headers.update(default_headers)
        if self.method == "GET":
            if self.params != {}:
                params = urllib.parse.urlencode(self.params)
                link = link + '?' + params
            req = urllib.request.Request(link, headers=self.headers, method=self.method)
        elif self.method == "POST":
            params = str(self.params).encode("utf-8")
            default_headers.update({"Content-Length": len(params)})
            req = urllib.request.Request(link, data=params, headers=self.headers, method=self.method)
        else:
            log.warn("Method--{method} not support now".format(method=self.method))
            return

        with urllib.request.urlopen(req) as file:
            contents = file.read().decode('utf-8')
            print(contents)
            if file.info().get('Content-Type') == "text/html":
                p = HtmlParser()
                p.feed(contents)
                for k in p.output_list:
                    _url = urldefrag(urlparse(urllib.parse.urljoin(link, k)).geturl()).url
                    self.list_add(self.links, _url)
            elif file.info().get('Content-Type') == "application/json":
                data = json.loads(contents)
                # special for api parse (api.kandao.tech)
                if data["code"] == 200:
                    p = JsonParser()
                    p.feed(contents)
                    # print(p.output_list)
                    for k in p.output_list:
                        _url = urldefrag(urlparse(urllib.parse.urljoin(link, k)).geturl()).url
                        self.list_add(self.links, _url)
                else:
                    log.error("{code}--{msg}".format(code=data["code"], msg=data["msg"]))
            else:
                log.info("Content-Type %s" % file.info().get('Content-Type'))

            # save path

            save_path = os.path.join(self.dir, url.netloc, url.path[1:] if url.path.startswith("/") else url.path)
            # create dir
            dir = os.path.dirname(save_path)
            if not os.path.exists(dir):
                os.makedirs(dir)
            if save_path.endswith("/"):
                save_path = os.path.join(save_path, "file")

            # extension
            filename = os.path.basename(save_path)
            ext = os.path.splitext(filename)[1]
            if ext == ".m3u8":
                p = HlsPraser(http_link=link)
                p.feed(contents)
                for k in p.output_list:
                    _url = urldefrag(urlparse(urllib.parse.urljoin(link, k)).geturl()).url
                    self.list_add(self.links, _url)

            # save
            with open(save_path, 'wb') as f:
                f.write(contents.encode("utf-8"))
                f.close()

            self.id += 1
            self.success.append(link)
            # cycle
            while len(self.links):
                self.download(self.links.pop(0))
                log.info(len(self.links))

    def download(self, http_link):
        """
        download file by http url and parse special type file to update download list
        :param http_link:
        :return:
        """
        url = urlparse(http_link)
        save_path = os.path.join(self.dir, url.netloc, url.path[1:] if url.path.startswith("/") else url.path)
        log.info("http_link=%s" % http_link)
        dir = os.path.dirname(save_path)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if save_path.endswith("/"):
            save_path = os.path.join(save_path, "file")

        filename = os.path.basename(save_path)
        ext = os.path.splitext(filename)[1]
        if ext != ".m3u8" and ext != "" and ext != ".html" and ext != ".htm":
            if os.path.exists(save_path):
                self.id += 1
                self.success.append(http_link)
                log.info("{path} exist.".format(path=save_path))
                return
        try:
            _http_link = urllib.parse.quote(http_link, safe=':/?&=')  # parse link to url
            data, headers = urllib.request.urlretrieve(url=_http_link, filename=save_path, reporthook=progress_callback)
            log.info("http_link=%s save_path=%s" % (_http_link, save_path))

            # parse special download file
            if headers["Content-Type"] == "text/html":
                p = HtmlParser()
                p.feed(open(data, "br").read().decode('utf-8'))
                for k in p.output_list:
                    _url = urldefrag(urlparse(urllib.parse.urljoin(_http_link, k)).geturl()).url
                    self.list_add(self.links, _url)
            elif headers["Content-Type"] == "application/json":
                p = JsonParser()
                p.feed(open(data, "br").read().decode('utf-8'))
                for k in p.output_list:
                    _url = urldefrag(urlparse(urllib.parse.urljoin(_http_link, k)).geturl()).url
                    self.list_add(self.links, _url)
            else:
                log.info("Content-Type %s" % headers["Content-Type"])

            if ext == ".m3u8":
                p = HlsPraser(http_link=http_link)
                p.feed(open(data, "br").read().decode('utf-8'))
                for k in p.output_list:
                    _url = urldefrag(urlparse(urllib.parse.urljoin(_http_link, k)).geturl()).url
                    self.list_add(self.links, _url)

            self.id += 1
            self.success.append(http_link)
        except Exception as e:
            log.error('Error--%s.' % str(e))
            self.id += 1
            self.failure.append(http_link)


    def run(self):
        log.info("start")
        if self.url_check(self.link):
            self.parse()
            log.info("total file %d" % self.id)
            log.info("download success: %d" % len(self.success))
            log.info("download failure: %s" % self.failure)


if __name__ == "__main__":

    # method POST just for x-www-form-urlencoded
    # params0 = {
    #     "version_name": "2.0.2.1",
    #     "version_code": 2021,
    #     "appkey": "3AD6-B93D-936F-D790-DBC9-86B6-108C-5DB5",
    #     "title": "KDSTUDIO"
    # }
    # headers0 = {
    #     "Content-Type": "application/json"
    # }
    #
    # downloader0 = Downloader("http://cms.kandao.tech/pkg/v1/patch/get", method="POST", params=json.dumps(params0),
    #                          headers=headers0, dst_dir="studio_2021")
    # downloader0.run()

    # method GET
    # case 1
    params1 = {
        "codec": 5,
        "container": "H",
        "language": "ZH-CN",
        "name": "test18",
        "vbr": 8,
        "warping": "C",
    }
    downloader1 = Downloader("https://cms.kandaovr.com/video/v1/playlist", params=params1, dst_dir="video_test18")
    downloader1.run()
    # case 2
    # downloader1 = Downloader("https://cms.kandaovr.com/video/v1/playlist?codec=5&container=H&language=ZH-CN&name=test18&vbr=8&warping=C", dst_dir="test")
    # downloader1.run()

    # # player pull playlist all videos --set page_count=100 now
    # downloader1 = Downloader(
    #     "https://api.kandaovr.com/video/v1/playlist?name=KANDAO_APP_MAIN&language=ZH-CN&page_count=100&page_num=0&codec=5&container=H&vbr=8&warping=C",
    #     dst_dir="video_KANDAO_APP_MAIN")
    # downloader1.run()

    # player pull album all photos --set page_count=100 now
    # downloader1 = Downloader(
    #     "https://api.kandaovr.com/photo/v1/album?name=KANDAO_APP_MAIN&language=ZH-CN&page_count=100&page_num=0",
    #     dst_dir="photo_KANDAO_APP_MAIN")
    # downloader1.run()

    # player pull livelist all channels --set page_count=100 now
    # downloader1 = Downloader(
    #     "https://api.kandaovr.com/live/v1/livelist?name=KANDAO_APP_MAIN&language=ZH-CN",
    #     dst_dir="live_KANDAO_APP_MAIN")
    # downloader1.run()

    # run a website
    # downloader2 = Downloader("https://kandaovr.com", dst_dir="website")
    # downloader2.run()

    # download m3u8 files
    # downloader3 = Downloader("https://v1.kandaovr.com/offcenter/H265/4M/temple1080p_3dv_offcenter.m3u8", dst_dir="m3u8")
    # downloader3.run()
    # downloader3 = Downloader("http://v3.kandaovr.com/H264/8M/huizhou_4kx4k_360x180_cube_lr.m3u8", dst_dir="m3u8")
    # downloader3.run()
    # downloader3 = Downloader("http://v1.kandaovr.com/offcenter/H265/8M/beijing_8k_3dv_offcenter.m3u8", dst_dir="m3u81")
    # downloader3.run()
    # downloader3 = Downloader("http://v3.kandaovr.com/H264/4M/temple_4kx4k_360x180_cube_mono.m3u8", dst_dir="m3u82")
    # downloader3.run()
    downloader1 = Downloader(
        "http://192.168.50.37/live/demo_8192x4096_360x180_offcube_mono.json",
        dst_dir="111")
    downloader1.run()


