# akamTester v6.0
批量测试 B 站海外 CDN（如 upos-hz-mirrorakam.akamaized.net）节点延迟，找出最低延迟节点，并生成可用于 hosts 加速的记录。

---

在 Hosts 中追加：
```
最低延迟的 IP upos-hz-mirrorakam.akamaized.net
最低延迟的IP upos-sz-mirroraliov.bilivideo.com
```

每次运行会输出形如：
```
104.116.243.32 upos-hz-mirrorakam.akamaized.net
155.102.4.143 upos-sz-mirroraliov.bilivideo.com
```

`*_iplist.txt` 文件用于缓存每个域名解析得到的 IP，当网络异常或解析失败时，会从对应的缓存文件中读取作为备用，确保各个域名数据互不干扰。

---

:warning: Windows 7 用户需使用管理员权限运行 :warning:

---

## EXE 文件运行
不熟悉 Python 的用户可从 [releases](https://github.com/miyouzi/akamTester/releases/latest) 页面下载可执行文件直接运行。

---

## 源码运行

安装依赖：

```bash
pip install -r requirements.txt
```

执行主程序：
```bash
python akamTester.py
```

---

## 指定测试域名

从 v6.0 起，支持同时指定多个测试域名：

```bash
python akamTester.py -u upos-sz-mirroraliov.bilivideo.com upos-hz-mirrorakam.akamaized.net
```

---

## 关于核心模块（轮子）

### GlobalDNS
`GlobalDNS` 是一个用于获取全球 DNS A 记录的解析类，整合了多个平台：

- dnschecker.org
- whatsmydns.net
- viewdns.info
- dnspropagation.net
- digwebinterface.com
- Cloudflare / Google / 阿里 / 腾讯 等公共 DNS 查询
- 自动解析 CNAME 并追踪最终 A 记录

**导入**
```python
from GlobalDNS import GlobalDNS
```

**使用**
```python
akam = GlobalDNS('upos-hz-mirrorakam.akamaized.net')
ip_list = akam.get_ip_list()  # 获取全球解析结果
akam.renew()  # 重新解析
ip_list = akam.get_ip_list()  # 获取更新后的结果
```
独立缓存文件（如 `upos-hz-mirrorakam.akamaized.net_iplist.txt`）用于存储每个域名的解析结果，确保多域名测试时数据独立。

---

### ColorPrinter
`ColorPrinter` 是一个终端彩色输出工具，支持红、绿及默认颜色，适配 Windows / Linux / VSCode 终端环境。

**导入**
```python
from ColorPrinter import color_print
```

**使用**
```python
color_print('普通输出')             # 默认颜色
color_print('错误输出', status=1)    # 红色
color_print('成功输出', status=2)    # 绿色
```

---

## 项目维护说明

本项目原由 [@Miyouzi](https://github.com/miyouzi) 创建。  
本版本由 [@oldip](https://github.com/oldip) 改进，加入以下核心功能：

- 多 DNS 平台整合
- 模拟 HTTPS 握手测速
- 支持多域名批量测试，每个域名独立缓存解析结果
- 自动筛选延迟 <200ms 节点并输出
- 使用 cloudscraper 替代 cfscrape，增强稳定性

欢迎提出改进建议与 PR。