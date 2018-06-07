# https://dev.maxmind.com/zh-hans/geoip/geoipupdate/
# https://github.com/maxmind/geoipupdate

import geoip2.database
from functools import reduce

reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
response = reader.country('128.101.101.101')
print(response)
print(response.country.iso_code)
reader.close()

reader = geoip2.database.Reader('GeoLite2-City.mmdb')
response = reader.city('47.89.181.11')
print(response)
print(response.country.iso_code)
reader.close()

reader = geoip2.database.Reader('GeoLite2-City.mmdb')
response = reader.city('116.24.67.128')
print(response)
print(response.country.iso_code)
reader.close()


def ip_into_int(ip):
    return reduce(lambda x, y: (x << 8) + y, map(int, ip.split('.')))

def is_internal_ip(ip):
    ip = ip_into_int(ip)
    net_a = ip_into_int('10.255.255.255') >> 24
    net_b = ip_into_int('172.31.255.255') >> 20
    net_c = ip_into_int('192.168.255.255') >> 16
    return ip >> 24 == net_a or ip >>20 == net_b or ip >> 16 == net_c


print(is_internal_ip("192.168.50.36"))