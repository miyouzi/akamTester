#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/7/19 16:52
# @Author  : Miyouzi
# @File    : akamTester.py
# @Software: PyCharm

from pythonping import ping
from ColorPrinter import color_print
from GlobalDNS import GlobalDNS

def ping_test(ip):
    result = ping(ip, count=5)
    delay = result.rtt_avg_ms
    msg = ip + '  平均延迟:   ' + str(delay) + ' ms'
    if delay<100:
        color_print(msg, status=2)
    else:
        color_print(msg)
    return delay

akam = GlobalDNS('upos-hz-mirrorakam.akamaized.net')

color_print('第一次解析:')
ip_list = akam.get_ip_list()
print()
color_print('第二次解析:')
akam.renew()
ip_list = ip_list | akam.get_ip_list()
print()

color_print('共取得 '+str(len(ip_list))+' 个 IP, 开始测试延迟')
print()
good_ips = []

for ip in akam.get_ip_list():
    delay = ping_test(ip)
    if delay < 100:
        good_ips.append({'ip':ip, 'delay':delay})
print()

color_print('基于当前网络环境, 以下为低延迟IP')
for ip in good_ips:
    color_print(ip['ip'] + '  平均延迟:   ' + str(ip['delay']) + ' ms', status=2)