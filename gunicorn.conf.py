# Gunicorn 配置文件
# 使用方式: gunicorn -c gunicorn.conf.py app:app

import multiprocessing
import os

# 服务器配置
bind = "0.0.0.0:10101"
workers = 1
worker_class = "sync"
timeout = 600
keepalive = 5

# 日志配置
accesslog = "./logs/access.log"
errorlog = "./logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = "PX_Tools"

# PID 文件
pidfile = "./logs/gunicorn.pid"

# 工作目录
chdir = os.path.dirname(os.path.abspath(__file__))

# 用户和组（如果需要，取消注释并修改）
# user = "ubuntu"
# group = "ubuntu"

# 守护进程模式（通过命令行参数 --daemon 控制，不在这里设置）

# 预加载应用（提高性能，但会增加内存使用）
preload_app = False

# 最大请求数（防止内存泄漏，0 表示不限制）
max_requests = 1000
max_requests_jitter = 50

# 优雅超时时间
graceful_timeout = 30

# 工作进程重启前的最大请求数
max_requests = 1000
max_requests_jitter = 50

# 工作进程空闲超时时间（秒）
timeout = 120

# 启用统计信息
statsd_host = None  # 如果使用 statsd，设置主机地址

# SSL 配置（如果需要 HTTPS，取消注释并配置）
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

