#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/7/19 14:26
# @Author  : Miyouzi
# @File    : GlobalDNS.py
# @Software: PyCharm

import requests, dns.resolver, json
from bs4 import BeautifulSoup
import re, time, socket
import concurrent.futures
import cfscrape
import json


class GlobalDNS():
    def __init__(self, domain, max_retry=3):
        self.__domain = domain
        self.__ip_list = set()
        self.__dns_id = set()
        self.__session = requests.session()
        self.__max_retry = max_retry
        self.__token = ''
        self.__init_header()
        self.__session.headers.update(self.__req_header)
        self.scraper = cfscrape.create_scraper()

    def __init_header(self):
        # 伪装为Chrome
        host = 'www.whatsmydns.net'
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'
        ref = 'https://' + host + '/'
        lang = 'zh-TW,zh;q=0.8,zh-HK;q=0.6,en-US;q=0.4,en;q=0.2'
        accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        accept_encoding = 'gzip, deflate'
        cache_control = 'no-cache'
        header = {
            "Host": host,
            "User-Agent": ua,
            "referer": ref,
            "Accept": accept,
            "Accept-Language": lang,
            "Accept-Encoding": accept_encoding,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": cache_control,
            "Cache-Control": cache_control,
            "TE": "Trailers"
        }
        self.__req_header = header

    def __request(self, url):
        error_cnt = 0
        while True:
            try:
                f = self.__session.get(url, timeout=10)
                break
            except requests.exceptions.RequestException as e:
                # print('请求出现异常')
                if error_cnt >= self.__max_retry:
                    raise e
                time.sleep(3)
                error_cnt += 1
        return BeautifulSoup(f.content, "lxml")

    def __get_dns_id(self):
        response = self.scraper.get('https://www.whatsmydns.net/api/servers')
        json_object= json.loads(response.content)
        self.__dns_id = set(map(lambda s: s['id'], json_object))

    def __extend_query(self):
        # 本地解析
        A = dns.resolver.query(self.__domain, 'A')
        for i in A:
            self.__ip_list.add(i.address)

        # 谷歌解析
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [socket.gethostbyname('8.8.4.4')]
        A = resolver.query(self.__domain, 'A')
        for i in A:
            self.__ip_list.add(i.address)

        # 腾讯解析
        resolver.nameservers = [socket.gethostbyname('119.29.29.29')]
        A = resolver.query(self.__domain, 'A')
        for i in A:
            self.__ip_list.add(i.address)

        # 阿里解析
        resolver.nameservers = [socket.gethostbyname('223.5.5.5')]
        A = resolver.query(self.__domain, 'A')
        for i in A:
            self.__ip_list.add(i.address)


    def __global_query(self):
        urls = []
        for dns_id in self.__dns_id:
            url = 'https://www.whatsmydns.net/api/details?server='+dns_id\
                  +'&type=A&query='+self.__domain
            urls.append(url)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scraper.get, url) for url in urls]
            results = [f.result() for f in futures]

        for res in results:
            try:
                details = json.loads(res.text)
                ip = details["data"][0]["response"]
                if isinstance(ip, list):
                    self.__ip_list = self.__ip_list | set(ip)  # set 并集
            except IndexError:
                pass
                # 该 DNS 失效

    def __global_query2(self):
        for dns_id in self.__dns_id:
            url = 'https://www.whatsmydns.net/api/details?server='+dns_id\
                  +'&type=A&query='+self.__domain
            try:
                text = self.__request(url).text
                details = json.loads(text)
                ip = details["data"][0]["response"]
                if isinstance(ip, list):
                    self.__ip_list = self.__ip_list | set(ip)  # set 并集
            except IndexError:
                pass
                # 该 DNS 失效

    def get_ip_list(self):

        if len(self.__ip_list) == 0:
            # 如果尚未解析
            self.renew()
        return self.__ip_list

    def renew(self):
        print('正在对 ' + self.__domain + ' 进行全球解析……')
        self.__session.cookies.clear()
        self.__get_dns_id()
        self.__global_query()
        self.__extend_query()
        print(self.__domain + ' 的全球解析已完成')


if __name__ == '__main__':
    import pprint
    a = GlobalDNS('upos-hz-mirrorakam.akamaized.net')
    b = a.get_ip_list()
    pprint.pprint(b)