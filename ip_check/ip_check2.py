import time,json
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.httpclient import HTTPRequest
import logging
logger = logging.getLogger("ip_check")

class IpCheck(object):
    HEADERS = {'Accept': 'text/xml;charset=UTF-8',
               'Accept-Encoding': 'gzip'}

    def __init__(self):
        self.http = AsyncHTTPClient()
        self.country_code = "CN"  # default

    @coroutine
    def get(self, url, timeout):
        request = HTTPRequest(url=url, method='GET', headers=IpCheck.HEADERS, connect_timeout=timeout,
                              request_timeout=timeout, follow_redirects=False, max_redirects=False,
                              user_agent="Mozilla/5.0+(Windows+NT+6.2;+WOW64)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/45.0.2454.101+Safari/537.36",)
        yield self.http.fetch(request, callback=self.find, raise_error=False)

    def find(self, response):
        if response.error:
            logger.error("response code={0} url={1} time_cost={2} error={3}".format(response.code, response.effective_url,
                                                                          response.request_time, response.error))
        else:
            logger.info("response code={0} url={1} time_cost={2}".format(response.code, response.effective_url,
                                                                         response.request_time))
            data = json.loads(response.body.decode("utf-8"))
            if "taobao" in response.effective_url:
                if data["code"] == 0:
                    self.country_code = data["data"]["country_id"]
            else:
                if data["status"] == "success":
                    self.country_code = data["countryCode"]
            logger.debug("country_code={0}".format(self.country_code))


class CheckProcess(object):

    def __init__(self, ip, timeout):
        self.a = IpCheck()
        self.urls = []
        self.urls.append("http://ip.taobao.com/service/getIpInfo.php?ip=" + ip)
        self.urls.append("http://ip-api.com/json/" + ip)
        self.code = "CN"
        self.timeout = timeout

    @coroutine
    def d(self):
        t1 = time.time()
        yield [self.a.get(url, self.timeout) for url in self.urls]
        t = time.time() - t1
        self.code = self.a.country_code
        logger.info("Process cost time: {0}".format(t))

if __name__ == '__main__':

    dd = CheckProcess("47.89.181.11", 0.4)
    loop = IOLoop.current()
    loop.run_sync(dd.d)
    print(dd.code)

    dd2 = CheckProcess("116.24.67.128", 0.4)
    loop = IOLoop.current()
    loop.run_sync(dd2.d)
    print(dd2.code)