#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/03/25
# @Author  : Miyouzi & oldip
# @File    : GlobalDNS.py
# @Software: PyCharm

import dns.resolver
import socket
import re
import concurrent.futures
import cloudscraper 
import json

class GlobalDNS():
    """
        同时透过多个 DNS 查询来源抓取全球 A 记录：
            1. 使用 dnschecker.org（网页爬虫方式）
            2. 使用 whatsmydns.net API
            3. 使用 viewdns.info、dnspropagation.net 与 digwebinterface.com（爬虫方式）
            4. 额外透过公共 DNS 伺服器查询
            5. 尝试解析 CNAME 指向的域名
        最后会过滤掉常见的公共 DNS 伺服器 IP（如 1.1.1.1、8.8.8.8、9.9.9.9 等），只保留解析到的目标域名 IP。
    """
    def __init__(self, domain):
        self.__domain = domain
        self.__ip_list = set()
        self.scraper = cloudscraper.create_scraper()
        
        # 额外的公共 DNS 伺服器 (这些将用来查询，但最终不纳入结果)
        self.__extra_dns_servers = [
            '8.8.8.8',         # Google
            '1.1.1.1',         # Cloudflare
            '9.9.9.9',         # Quad9
            '208.67.222.222',  # OpenDNS
            '119.29.29.29',    # 腾讯DNS
            '223.5.5.5',       # 阿里DNS
            '77.88.8.8',       # Yandex DNS
            '168.95.1.1',      # HiNet DNS
            '8.26.56.26',      # Comodo Secure DNS
            '64.6.64.6',       # Verisign Public DNS
            '94.140.14.14',    # AdGuard DNS
            '165.87.13.129',   # AT&T
            '192.76.144.66',   # Sonic.net
            '198.6.100.25',    # BBN Planet
            '158.43.240.3'     # Verizon/UUNet
        ]
        # 创建过滤集合，包括额外 DNS 服务器和额外指定的过滤规则
        self.__dns_filter_set = self.__get_dns_filter_set()
        
    def __get_dns_filter_set(self):
        """
        返回用于过滤解析结果中 DNS 服务器 IP 的集合，
        """
        filter_set = set(self.__extra_dns_servers)
        filter_set.add("8.8.4.4") # Google DNS
        filter_set.add("1.0.0.1") # Cloudflare DNS
        filter_set.add("9.9.9.10") # Quad9 DNS
        filter_set.add("208.67.220.220") # OpenDNS
        filter_set.add("168.95.192.1") # HiNet DNS
        filter_set.add("8.20.247.20") # Comodo Secure DNS
        filter_set.add("64.6.65.6") # Verisign Public DNS
        filter_set.add("94.140.15.15") # AdGuard DNS
        filter_set.add("195.129.12.122") # OpenNIC
        filter_set.add("1.25.625.625") # 错误的提取
        filter_set.add("8.25.82.*") # CleanBrowsing 匹配所有以 8.25.82. 开头的 IP
        filter_set.add("208.167.252.236") # 不明，自架 DNS 可能性高
        filter_set.add("144.217.51.168") # 不常见，但出现在 OpenNIC
        
        return filter_set


    def __scrape_dnschecker(self):
        base_url = "https://dnschecker.org/dns-checker.php"
        params = {
            "query": self.__domain,
            "type": "A",
            "dns": "All"
        }
        try:
            resp = self.scraper.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                return
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            ip_matches = ip_pattern.findall(resp.text)
            for ip in ip_matches:
                self.__ip_list.add(ip)
        except Exception as e:
            print(f"抓取 dnschecker.org 失败: {e}")


    def __scrape_whatsmydns(self):
        try:
            url_servers = "https://www.whatsmydns.net/api/servers"
            response = self.scraper.get(url_servers, timeout=10)
            servers_json = json.loads(response.content)
            server_ids = [server['id'] for server in servers_json]
            def query_server(server_id):
                url = f"https://www.whatsmydns.net/api/details?server={server_id}&type=A&query={self.__domain}"
                r = self.scraper.get(url, timeout=10)
                try:
                    details = json.loads(r.text)
                    ip_list = details.get("data", [])[0].get("response", [])
                    if isinstance(ip_list, list):
                        return ip_list
                except Exception:
                    return []
                return []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(query_server, server_ids)
            for result in results:
                for ip in result:
                    self.__ip_list.add(ip)
        except Exception as e:
            print(f"抓取 whatsmydns.net 失败: {e}")


    def __scrape_viewdns(self):
        base_url = "https://viewdns.info/propagation/"
        params = {"domain": self.__domain}
        try:
            resp = self.scraper.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                return
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            ip_matches = ip_pattern.findall(resp.text)
            for ip in ip_matches:
                self.__ip_list.add(ip)
        except Exception as e:
            print(f"抓取 viewdns.info 失败: {e}")


    def __scrape_dnspropagation(self):
        base_url = "https://www.dnspropagation.net/"
        params = {"domain": self.__domain}
        try:
            resp = self.scraper.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                return
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            ip_matches = ip_pattern.findall(resp.text)
            for ip in ip_matches:
                self.__ip_list.add(ip)
        except Exception as e:
            print(f"抓取 dnspropagation.net 失败: {e}")


    def __scrape_digwebinterface(self):
        base_url = "https://www.digwebinterface.com/"
        params = {"q": self.__domain, "type": "A"}
        try:
            resp = self.scraper.get(base_url, params=params, timeout=10)
            if resp.status_code != 200:
                return
            ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
            ip_matches = ip_pattern.findall(resp.text)
            for ip in ip_matches:
                self.__ip_list.add(ip)
        except Exception as e:
            print(f"抓取 digwebinterface.com 失败: {e}")


    def __extra_dns_query(self):
        for dns_server in self.__extra_dns_servers:
            try:
                resolver = dns.resolver.Resolver()
                resolver.nameservers = [socket.gethostbyname(dns_server)]
                answers = resolver.resolve(self.__domain, 'A')
                for rdata in answers:
                    self.__ip_list.add(rdata.address)
            except Exception:
                pass


    def __resolve_cname(self):
        try:
            cname_answers = dns.resolver.resolve(self.__domain, 'CNAME')
            for cname_record in cname_answers:
                cname_domain = cname_record.target.to_text().rstrip('.')
                for dns_server in self.__extra_dns_servers:
                    try:
                        resolver = dns.resolver.Resolver()
                        resolver.nameservers = [socket.gethostbyname(dns_server)]
                        answers = resolver.resolve(cname_domain, 'A')
                        for rdata in answers:
                            self.__ip_list.add(rdata.address)
                    except:
                        pass
        except:
            pass


    def get_ip_list(self):
        if not self.__ip_list:
            # 如果尚未解析
            self.renew()
        # 过滤掉已知的 DNS 伺服器 IP
        filtered_ips = set()
        for ip in self.__ip_list:
            # 如果 ip 精确匹配过滤集合中的任意一个（不含通配符），则跳过
            if ip in self.__dns_filter_set:
                continue
            # 如果过滤集合中有通配符模式，则检查 ip 是否匹配
            skip = False
            for filter_item in self.__dns_filter_set:
                if "*" in filter_item:
                    prefix = filter_item.replace("*", "")
                    if ip.startswith(prefix):
                        skip = True
                        break
            if skip:
                continue
            filtered_ips.add(ip)
        return filtered_ips

    def renew(self):
        print(f"正在同时透过多个来源抓取 {self.__domain} 的全球解析结果…")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            futures.append(executor.submit(self.__scrape_dnschecker))
            futures.append(executor.submit(self.__scrape_whatsmydns))
            futures.append(executor.submit(self.__scrape_viewdns))
            futures.append(executor.submit(self.__scrape_dnspropagation))
            futures.append(executor.submit(self.__scrape_digwebinterface))
            for future in concurrent.futures.as_completed(futures):
                future.result()
        self.__extra_dns_query()
        self.__resolve_cname()
        print(f"{self.__domain} 的全球解析已完成，共获得 {len(self.__ip_list)} 个 IP")


if __name__ == '__main__':
    test_domain = 'upos-hz-mirrorakam.akamaized.net'
    gd = GlobalDNS(test_domain)
    ip_list = gd.get_ip_list()
    print(f"最终取得 {len(ip_list)} 个 IP：", ip_list)