# QQ邮箱发送服务端

基于 Flask 的 QQ 邮箱发送服务，提供 HTTP API 接口用于发送邮件。

## 功能特性

- ✅ 使用 QQ 邮箱 SMTP 服务发送邮件
- ✅ RESTful API 接口
- ✅ 支持纯文本和 HTML 格式邮件
- ✅ 健康检查接口
- ✅ 错误处理和日志记录

## 环境要求

- Python 3.7+
- QQ 邮箱账号（需要开启 SMTP 服务并获取授权码）

## 快速开始

### 1. 克隆或下载项目

```bash
cd /home/ubuntu/Mail-Sender
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，填写你的 QQ 邮箱配置：

```env
QQ_EMAIL=your_qq_email@qq.com
QQ_PASSWORD=your_qq_auth_code
```

**重要：如何获取 QQ 邮箱授权码**

1. 登录 QQ 邮箱：https://mail.qq.com
2. 点击右上角「设置」->「账户」
3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」部分
4. 开启「POP3/SMTP服务」或「IMAP/SMTP服务」
5. 点击「生成授权码」，按照提示发送短信验证
6. 将生成的授权码复制到 `.env` 文件的 `QQ_PASSWORD` 字段

**注意：授权码不是你的 QQ 密码，而是一个独立的密码。**

### 5. 运行服务

```bash
python app.py
```

服务将在 `http://0.0.0.0:10101` 启动。

## API 接口文档

### 1. 健康检查

**接口地址：** `GET /health`

**响应示例：**

```json
{
  "status": "ok",
  "message": "服务运行正常"
}
```

### 2. 通用 LLM 提问

**接口地址：** `POST /llm/ask`

**请求头：**

```
Content-Type: application/json
```

**请求体：**

```json
{
  "question": "必填，提问文本",
  "model": "可选，模型名称，默认 qwen-plus",
  "enable_search": true
}
```

**成功响应示例：**

```json
{
  "success": true,
  "message": "调用成功",
  "data": {
    "answer": "模型原始回答文本",
    "model": "qwen-plus",
    "enable_search": true
  }
}
```

**失败响应示例：**

```json
{
  "success": false,
  "message": "LLM 调用失败",
  "error": "错误信息"
}
```

**HTTP 状态码：**
- `200`: 调用成功
- `400`: 参数错误（如 question 为空）
- `500`: 服务器或 LLM 调用失败

### 3. 发送邮件

**接口地址：** `POST /send`

**请求头：**

```
Content-Type: application/json
```

**请求体：**

```json
{
  "to_email": "target@example.com",
  "subject": "邮件主题",
  "content": "邮件内容",
  "content_type": "text"
}
```

**参数说明：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| to_email | string | 是 | 目标邮箱地址 |
| subject | string | 否 | 邮件主题，默认为"无主题" |
| content | string | 是 | 邮件内容 |
| content_type | string | 否 | 内容类型，可选值：`text`（纯文本）或 `html`（HTML格式），默认为 `text` |

**成功响应示例：**

```json
{
  "success": true,
  "message": "邮件发送成功",
  "data": {
    "to_email": "target@example.com",
    "subject": "邮件主题"
  }
}
```

**失败响应示例：**

```json
{
  "success": false,
  "message": "错误信息"
}
```

**HTTP 状态码：**

- `200`: 发送成功
- `400`: 请求参数错误
- `500`: 服务器错误或发送失败

## 使用示例

### 使用 curl 发送邮件

```bash
curl -X POST http://localhost:10101/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "recipient@example.com",
    "subject": "测试邮件",
    "content": "这是一封测试邮件",
    "content_type": "text"
  }'
```

### 使用 Python requests 发送邮件

```python
import requests

url = "http://localhost:10101/send"
data = {
    "to_email": "recipient@example.com",
    "subject": "测试邮件",
    "content": "这是一封测试邮件",
    "content_type": "text"
}

response = requests.post(url, json=data)
print(response.json())
```

### 发送 HTML 格式邮件

```bash
curl -X POST http://localhost:10101/send \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "recipient@example.com",
    "subject": "HTML邮件",
    "content": "<h1>标题</h1><p>这是HTML格式的邮件内容</p>",
    "content_type": "html"
  }'
```

## 生产环境部署

### 使用管理脚本（推荐）

项目提供了便捷的管理脚本 `manage.sh`，支持启动、停止、重启和查看状态。

1. 确保脚本有执行权限：

```bash
chmod +x manage.sh
```

2. 使用管理脚本：

```bash
# 启动服务
./manage.sh start

# 停止服务
./manage.sh stop

# 重启服务
./manage.sh restart

# 查看服务状态
./manage.sh status

# 查看日志
./manage.sh logs error    # 查看错误日志
./manage.sh logs access   # 查看访问日志
```

管理脚本会自动：
- 检测并激活虚拟环境
- 检查 gunicorn 是否安装
- 创建日志目录
- 以守护进程模式运行服务

### 使用 Gunicorn 配置文件

项目提供了 `gunicorn.conf.py` 配置文件，可以使用配置文件启动：

```bash
gunicorn -c gunicorn.conf.py app:app
```

### 使用 Gunicorn 直接启动

1. 安装 Gunicorn：

```bash
pip install gunicorn
```

2. 启动服务：

```bash
gunicorn -w 1 -b 0.0.0.0:10101 app:app
```

参数说明：
- `-w 1`: 启动 1 个工作进程
- `-b 0.0.0.0:10101`: 绑定地址和端口

### 使用 systemd 管理服务

创建服务文件 `/etc/systemd/system/mail-sender.service`：

```ini
[Unit]
Description=QQ Mail Sender Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Mail-Sender
Environment="PATH=/home/ubuntu/Mail-Sender/venv/bin"
ExecStart=/home/ubuntu/Mail-Sender/venv/bin/gunicorn -c /home/ubuntu/Mail-Sender/gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable mail-sender
sudo systemctl start mail-sender
```

查看服务状态：

```bash
sudo systemctl status mail-sender
```

查看日志：

```bash
sudo journalctl -u mail-sender -f
```

### 使用 Nginx 反向代理（可选）

如果需要通过域名访问，可以配置 Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:10101;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 防火墙配置

如果服务器开启了防火墙，需要开放 10101 端口：

**UFW (Ubuntu):**

```bash
sudo ufw allow 10101/tcp
```

**firewalld (CentOS/RHEL):**

```bash
sudo firewall-cmd --permanent --add-port=10101/tcp
sudo firewall-cmd --reload
```

## 故障排查

### 1. 邮箱认证失败

- 检查 `.env` 文件中的 `QQ_EMAIL` 和 `QQ_PASSWORD` 是否正确
- 确认使用的是授权码而不是 QQ 密码
- 确认已开启 QQ 邮箱的 SMTP 服务

### 2. 连接超时

- 检查服务器网络连接
- 确认防火墙规则允许访问
- 检查 QQ 邮箱 SMTP 服务是否正常

### 3. 端口被占用

```bash
# 检查端口占用
sudo netstat -tlnp | grep 10101
# 或
sudo lsof -i :10101
```

## 安全建议

1. **不要将 `.env` 文件提交到版本控制系统**
2. **在生产环境中使用 HTTPS**（通过 Nginx 配置 SSL）
3. **限制 API 访问**（使用防火墙或 API 密钥）
4. **定期更换 QQ 邮箱授权码**
5. **监控服务日志**，及时发现异常

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。

