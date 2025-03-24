#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2025/03/25
# @Author  : Miyouzi & oldip
# @File    : akamTester.py
# @Software: PyCharm

import os
import sys
import argparse
import socket
import time
import concurrent.futures
import ssl

from ColorPrinter import color_print
from GlobalDNS import GlobalDNS

working_dir = os.path.dirname(os.path.realpath(__file__))
# working_dir = os.path.dirname(sys.executable)  # 使用 pyinstaller 编译时，打开此项
# ip_list_path = os.path.join(working_dir, 'ip_list.txt')
version = 6.0

def normalize_host(host):
    """去除 URL 协议与尾部斜线"""
    if host.startswith("http://"):
        host = host[len("http://"):]
    elif host.startswith("https://"):
        host = host[len("https://"):]
    return host.rstrip("/")


def https_test(ip, host, port=443, max_retries=5):
    """
    使用 TLS 握手模拟 HTTPS 体验：针对指定 IP 建立一个带有 SNI（host）的 SSL/TLS 连线，
    测量从建立 TCP 连线到握手完成的总延迟（毫秒）。
    若失败则重试 max_retries 次。
    """
    attempts = 0
    delay = float('inf')
    while attempts < max_retries:
        try:
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(5)  # 超时设定为 5 秒
            start = time.time()
            raw_sock.connect((ip, port))
            context = ssl.create_default_context()
            ssl_sock = context.wrap_socket(raw_sock, server_hostname=host)
            end = time.time()
            delay = (end - start) * 1000  # 转换为毫秒
            ssl_sock.close()
            break  # 成功连线则退出
        except Exception as e:
            attempts += 1
    msg = f"{ip}\tHTTPS连接延迟: {delay:.1f} ms"
    if delay < 200:
        color_print(msg, status=2)
    else:
        color_print(msg)
    return delay


def process_host(host):
    """针对单一域名进行解析与 HTTPS 连接测试"""
    normalized_host = normalize_host(host)
    # 使用独立的缓存文件保存解析到的 IP
    host_cache_file = os.path.join(working_dir, normalized_host + "_iplist.txt")
    low_delay_ip_list_path = os.path.join(working_dir, normalized_host + '.txt')

    color_print(f"\n当前测试域名：{normalized_host}", status=2)
    try:
        gd = GlobalDNS(normalized_host)
        color_print('第一次解析:')
        ip_set = gd.get_ip_list()

        # 額外多次解析以收集更多 IP（可根據需要調整次數）
        extra_renew_times = 2
        for i in range(extra_renew_times):
            color_print(f'第 {i+2} 次解析:')
            gd.renew()
            ip_set.update(gd.get_ip_list())
    except Exception as e:
        color_print(f'进行全球解析时遇到未知错误: {e}', status=1)
        if os.path.exists(host_cache_file):
            color_print('将读取本地保存的 IP 列表', status=1)
            with open(host_cache_file, 'r', encoding='utf-8') as f:
                ip_set = set(line.strip() for line in f if line.strip())
        else:
            color_print('没有本地保存的 IP 列表！程序终止！', status=1)
            sys.exit(0)
    else:
        with open(host_cache_file, 'w', encoding='utf-8') as f:
            for ip in ip_set:
                f.write(ip + '\n')

    color_print(f'\n共取得 {len(ip_set)} 个 IP, 开始测试 HTTPS 连接延迟', status=2)

    ip_info = []
    good_ips = []
    # 使用 ThreadPoolExecutor 来并发测试每个 IP 的 HTTPS 连线延迟
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_map = {executor.submit(https_test, ip, normalized_host): ip for ip in ip_set}
        for future in concurrent.futures.as_completed(future_map):
            ip = future_map[future]
            delay = future.result()
            ip_info.append({'ip': ip, 'delay': delay})
            if delay < 200:
                good_ips.append({'ip': ip, 'delay': delay})

    print()
    if good_ips:
        color_print('基于当前网络环境, 以下为 HTTPS 连接延迟低于200ms的IP', status=2)
        good_ips.sort(key=lambda x: x['delay'])
        with open(low_delay_ip_list_path, 'w', encoding='utf-8') as f:
            for item in good_ips:
                color_print(f"{item['ip']}\tHTTPS连接延迟: {item['delay']:.1f} ms", status=2)
                f.write(item['ip'] + ' ' + normalized_host + '\n')
    else:
        ip_info.sort(key=lambda x: x['delay'])
        num = min(3, len(ip_info))
        color_print(f'本次测试未能找到 HTTPS 连接延迟低于200ms的IP! 以下为延迟最低的 {num} 个节点', status=1)
        for i in range(num):
            color_print(f"{ip_info[i]['ip']}\tHTTPS连接延迟: {ip_info[i]['delay']:.1f} ms", status=1)

    color_print("------------------------------------------------------------", status=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_hosts', '-u', nargs='+', 
                        help='指定测试域名列表（空格分隔）',
                        default=['upos-sz-mirroraliov.bilivideo.com', 'upos-hz-mirrorakam.akamaized.net'],
                        required=False)
    args = parser.parse_args()
    hosts = args.user_hosts

    version_msg = f'当前 akamTester 版本: {version}'
    color_print(version_msg, status=2)

    for host in hosts:
        process_host(host)

    input('按回车退出')
    sys.exit(0)

if __name__ == '__main__':
    main()