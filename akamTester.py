#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/7/19 16:52
# @Author  : Miyouzi
# @File    : akamTester.py
# @Software: PyCharm

from pythonping import ping
from ColorPrinter import color_print
from GlobalDNS import GlobalDNS
from shutil import copyfile
from hosts import Hosts, HostsEntry
from filecmp import cmp
from time import sleep
import sys
import os
import argparse

working_dir = os.path.dirname(os.path.realpath(__file__))
# working_dir = os.path.dirname(sys.executable)  # 使用 pyinstaller 编译时，打开此项
ip_list_path = os.path.join(working_dir, 'ip_list.txt')
version = 4.1
version = 5.0


def ping_test(ip):
    result = ping(ip, count=5)
    delay = result.rtt_avg_ms
    msg = ip + '\t平均延迟: ' + str(delay) + ' ms'
    if delay < 100:
        color_print(msg, status=2)
    else:
        color_print(msg)
    return delay


version_msg = '当前akamTester版本: ' + str(version)
color_print(version_msg, 2)
host = 'upos-hz-mirrorakam.akamaized.net'

# 支持命令行, 允许用户通过参数指定测试域名
parser = argparse.ArgumentParser()
parser.add_argument('--user_host', '-u', type=str,
                    help='指定测试域名', default=host, required=False)
#增加通过命令行添加至hosts的选项
parser.add_argument('--to_host', '-t',action="store_true",
                    help='将最快的解析结果添加至hosts', required=False)                    
arg = parser.parse_args()
if arg.user_host:
    host = arg.user_host

try:
    akam = GlobalDNS(host)
    color_print('第一次解析:')
    ip_list = akam.get_ip_list()
    print()
    color_print('第二次解析:')
    akam.renew()
    ip_list = ip_list | akam.get_ip_list()
    print()
    color_print('第三次解析:')
    akam.renew()
    ip_list = ip_list | akam.get_ip_list()
except BaseException as e:
    color_print('进行全球解析时遇到未知错误: '+str(e), status=1)
    if os.path.exists(ip_list_path):
        color_print('将读取本地保存的ip列表', status=1)
        with open(ip_list_path, 'r', encoding='utf-8') as f:
            ip_list = f.read().splitlines()
    else:
        color_print('没有本地保存的ip列表！程序终止！', status=1)
        print()
        input('按回车退出')
        sys.exit(0)
else:
    # 保存解析结果
    with open(ip_list_path, 'w', encoding='utf-8') as f:
        for ip in ip_list:
            f.write(str(ip))
            f.write('\n')

print()
color_print('共取得 '+str(len(ip_list))+' 个 IP, 开始测试延迟')
print()

ip_info = []
good_ips = []

for ip in ip_list:
    delay = ping_test(ip)
    ip_info.append({'ip': ip, 'delay': delay})
    if delay < 100:
        good_ips.append({'ip': ip, 'delay': delay})
print()

if len(good_ips) > 0:
    color_print('基于当前网络环境, 以下为延迟低于100ms的IP', status=2)
    good_ips.sort(key=lambda x: x['delay'])
    for ip in good_ips:
        color_print(ip['ip'] + '\t平均延迟: ' + str(ip['delay']) + ' ms', status=2)
else:
    ip_info.sort(key=lambda x: x['delay'])
    color_print('本次测试未能找到延迟低于100ms的IP! 以下为延迟最低的 3 个节点', status=1)
    for i in range(0, 3):
        color_print(ip_info[i]['ip'] + '\t平均延迟: ' +
                    str(ip_info[i]['delay']) + ' ms')
# 新增加功能:写入hosts
if arg.to_host:
    #创建hosts备份文件
    fol=os.getcwd()
    hostsFolder = os.environ['systemroot']+"\\System32\\drivers\\etc"#从系统变量读取 防止出现用户的系统不在C盘的情况
    copyfile(hostsFolder+"\\hosts", fol+"\\hosts_bak")
    if len(good_ips) > 0:
        fastest_ip= good_ips[0]['ip']
    else:
        fastest_ip=  ip_info[0]['ip']
    #编码处理
    try:
        open(hostsFolder+"\\hosts", 'r')
        pass
    except ValueError:
        color_print('请尝试将您的Hosts文件保存为UTF-8 with BOM编码',status=1)
        color_print('您可以尝试将 '+ fastest_ip +' '+host+' 拷贝到hosts文件最后一行，您的Hosts文件路径为 '+hostsFolder+"\\hosts")
    else:
        pass
    #Hosts文件操作
    fastHosts = Hosts()
    fastHosts.remove_all_matching(name=host)
    new_entry = HostsEntry(entry_type='ipv4', address=fastest_ip, names=[host])
    du=fastHosts.add([new_entry])
    fastHosts.write()    
    #判断是否修改成功
    if cmp(hostsFolder+"\\hosts", fol+"\\hosts_bak") & du['duplicate_count']==0:
        color_print("好像出现错误了，请尝试手动添加！", status=1)
    else:
        color_print("成功添加", status=2)
        os.system('ipconfig /flushdns')
print()
input('按回车退出')
sys.exit(0)