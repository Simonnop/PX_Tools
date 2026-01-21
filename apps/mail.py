import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# QQ邮箱SMTP配置
QQ_SMTP_SERVER = "smtp.qq.com"
QQ_SMTP_PORT = 587

# 从环境变量获取邮箱配置
QQ_EMAIL = os.getenv("QQ_EMAIL", "")
QQ_PASSWORD = os.getenv("QQ_PASSWORD", "")  # QQ邮箱授权码


def send_email(to_email, subject, content, content_type="text"):
    """
    发送邮件
    
    Args:
        to_email: 目标邮箱地址
        subject: 邮件主题
        content: 邮件内容
        content_type: 内容类型，'text' 或 'html'
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not QQ_EMAIL or not QQ_PASSWORD:
        return False, "邮箱配置未设置，请检查环境变量 QQ_EMAIL 和 QQ_PASSWORD"
    
    if not to_email:
        return False, "目标邮箱地址不能为空"
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        # 使用 formataddr 确保 From 头符合 RFC5322 标准
        msg['From'] = formataddr(("Simonnop's Mail Bot", QQ_EMAIL))
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加邮件正文
        if content_type == "html":
            msg.attach(MIMEText(content, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        # 连接SMTP服务器并发送
        server = smtplib.SMTP(QQ_SMTP_SERVER, QQ_SMTP_PORT)
        server.starttls()  # 启用TLS加密
        server.login(QQ_EMAIL, QQ_PASSWORD)
        server.sendmail(QQ_EMAIL, [to_email], msg.as_string())
        server.quit()
        
        return True, "邮件发送成功"
    
    except smtplib.SMTPAuthenticationError:
        return False, "邮箱认证失败，请检查QQ邮箱和授权码是否正确"
    except smtplib.SMTPRecipientsRefused:
        return False, "目标邮箱地址无效或被拒绝"
    except smtplib.SMTPServerDisconnected:
        return False, "SMTP服务器连接断开"
    except Exception as e:
        return False, f"发送邮件时发生错误: {str(e)}"
