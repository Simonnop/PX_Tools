#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ邮箱发送服务端
提供HTTP接口用于发送邮件
"""

from flask import Flask, request, jsonify
from apps.mail import send_email
from apps.llm import ask_llm

app = Flask(__name__)
# 让 jsonify 输出中文不被 \uXXXX 转义（Flask 2/3 兼容写法）
app.config["JSON_AS_ASCII"] = False
try:
    app.json.ensure_ascii = False
except Exception:
    pass

@app.route('/health_check', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "message": "服务运行正常"
    }), 200


@app.route('/llm/ask', methods=['POST'])
def llm_ask():
    """
    通用提问接口

    请求体 JSON:
    {
        "question": "必填，提问文本",
        "model": "可选，模型名称，默认 qwen-plus",
        "enable_search": false  // 可选，是否启用检索，默认 false
    }

    返回:
        JSON 统一结构:
        {
            "success": true/false,
            "message": "提示信息",
            "data": {
                "answer": "LLM 原始回答",
                "model": "qwen-plus",
                "enable_search": true
            }   // 仅 success=true 时存在
            "error": "错误信息" // 仅 success=false 时存在
        }
    """
    try:
        data = request.get_json(silent=True) or {}
        question = data.get("question")
        model = data.get("model") or "qwen-plus"
        enable_search = data.get("enable_search", False)

        if not question or not str(question).strip():
            return jsonify({
                "success": False,
                "message": "question 不能为空"
            }), 400

        success, result = ask_llm(question, model=model, enable_search=enable_search)

        if success:
            return jsonify({
                "success": True,
                "message": "调用成功",
                "data": {
                    "answer": result,
                    "model": model,
                    "enable_search": bool(enable_search)
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "LLM 调用失败",
                "error": result
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"处理请求时发生错误: {str(e)}"
        }), 500


@app.route('/send_email', methods=['POST'])
def send_mail():
    """
    发送邮件接口
    
    请求体JSON格式:
    {
        "to_email": "target@example.com",
        "subject": "邮件主题",
        "content": "邮件内容",
        "content_type": "text"  // 可选，默认为 "text"，可选 "html"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "请求体不能为空，请提供JSON数据"
            }), 400
        
        # 获取参数
        to_email = data.get('to_email')
        subject = data.get('subject', '无主题')
        content = data.get('content')
        content_type = data.get('content_type', 'text')
        
        # 验证必填参数
        if not to_email:
            return jsonify({
                "success": False,
                "message": "参数错误：to_email 不能为空"
            }), 400
        
        if not content:
            return jsonify({
                "success": False,
                "message": "参数错误：content 不能为空"
            }), 400
        
        # 发送邮件
        success, message = send_email(to_email, subject, content, content_type)
        
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "data": {
                    "to_email": to_email,
                    "subject": subject
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": message
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"处理请求时发生错误: {str(e)}"
        }), 500


if __name__ == '__main__':
    # 启动服务
    app.run(host='0.0.0.0', port=10101, debug=False)

