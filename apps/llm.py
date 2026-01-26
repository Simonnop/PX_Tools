import os
import shutil
import tempfile
from typing import Iterable, List

from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.datastructures import FileStorage
import fitz  # PyMuPDF
import dashscope
from dashscope import MultiModalConversation

# 加载环境变量
load_dotenv()

# 设置 dashscope base_url（北京地域）
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"


def _get_openai_client():
    """创建 OpenAI 客户端（阿里云百炼兼容接口）"""
    # 兼容部分环境：如果存在 HTTP(S)_PROXY 等代理变量，OpenAI SDK 可能会走 proxies 参数路径；
    # 而某些旧版依赖会导致报错：Client.__init__() got an unexpected keyword argument 'proxies'
    # 这里做保守处理：在本进程内移除代理变量，避免触发该路径。
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        os.environ.pop(k, None)
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("环境变量 DASHSCOPE_API_KEY 未配置")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    return client


def ask_llm(question: str, model: str = "qwen-plus", enable_search: bool = True):
    """
    直接向大模型提问，返回原始回答文本。

    参数:
        question: 必填，用户提问文本
        model: 可选，模型名称，默认 "qwen-plus"
        enable_search: 是否开启搜索，默认 True

    返回:
        (success: bool, result: str)
        success 为 True 时，result 为 LLM 原始回答
        success 为 False 时，result 为错误信息
    """
    if not question or not str(question).strip():
        return False, "question 不能为空"

    try:
        client = _get_openai_client()
        extra = {"extra_body": {"enable_search": bool(enable_search)}} if enable_search else {}

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question},
            ],
            **extra,
        )

        content = completion.choices[0].message.content
        return True, content

    except Exception as e:
        return False, str(e)


def _pdf_to_images(pdf_path: str, output_dir: str = None) -> List[str]:
    """
    将 PDF 文件转换为图片列表
    
    参数:
        pdf_path: PDF 文件路径
        output_dir: 输出目录，如果为 None 则使用临时目录
        
    返回:
        图片文件路径列表
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    elif not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_doc = fitz.open(pdf_path)
    image_paths = []
    
    try:
        for pg in range(pdf_doc.page_count):
            page = pdf_doc[pg]
            rotate = int(0)
            # 缩放系数，提高图片分辨率
            zoom_x = 1.33333333
            zoom_y = 1.33333333
            mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            image_path = os.path.join(output_dir, f'images_{pg}.png')
            pix.save(image_path)
            image_paths.append(f"file://{os.path.abspath(image_path)}")
    finally:
        pdf_doc.close()
    
    return image_paths


def _ask_vision_model(question: str, image_paths: List[str], model: str = "qwen3-vl-plus", fps: int = 2):
    """
    使用视觉模型 API 进行问答
    
    参数:
        question: 问题文本
        image_paths: 图片路径列表（file:// 格式）
        model: 模型名称，默认 qwen3-vl-plus
        fps: 视频帧率，适用于 Qwen2.5-VL 和 Qwen3-VL 系列模型
        
    返回:
        (success: bool, result: str)
    """
    try:
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            return False, "环境变量 DASHSCOPE_API_KEY 未配置"
        
        messages = [{
            'role': 'user',
            'content': [
                {'video': image_paths, "fps": fps},
                {'text': question}
            ]
        }]
        
        response = MultiModalConversation.call(
            api_key=api_key,
            model=model,
            messages=messages
        )
        
        if response and response.output and response.output.choices:
            message = response.output.choices[0].message
            if message.content and len(message.content) > 0:
                content_item = message.content[0]
                if isinstance(content_item, dict) and "text" in content_item:
                    content = content_item["text"]
                elif isinstance(content_item, str):
                    content = content_item
                else:
                    content = str(content_item)
                return True, content
            else:
                return False, "视觉模型 API 返回内容为空"
        else:
            return False, "视觉模型 API 返回结果为空"
            
    except Exception as e:
        return False, f"调用视觉模型 API 失败: {str(e)}"


def ask_llm_with_files(question: str, files: Iterable[FileStorage]):
    """
    使用 qwen-long 模型并携带上传文件进行问答，禁用联网搜索。
    如果传入的是单独的 PDF 文件，则先解析为图片列表，再使用视觉模型 API 处理。
    """
    if not question or not str(question).strip():
        return False, "question 不能为空"

    file_list = [f for f in files or [] if f and getattr(f, "filename", "")]
    if not file_list:
        return False, "files 不能为空"

    # 检查是否为单独的 PDF 文件
    print(file_list)
    print(len(file_list))

    
    if len(file_list) == 1:
        file = file_list[0]
        filename = getattr(file, "filename", "").lower()
        if filename.endswith('.pdf'):
            # 处理 PDF 文件：转换为图片并使用视觉模型
            temp_pdf_path = None
            temp_image_dir = None
            try:
                # 保存 PDF 到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    file.stream.seek(0)
                    tmp_pdf.write(file.stream.read())
                    temp_pdf_path = tmp_pdf.name
                
                # 创建临时目录存放图片
                temp_image_dir = tempfile.mkdtemp()
                
                # 将 PDF 转换为图片列表
                image_paths = _pdf_to_images(temp_pdf_path, temp_image_dir)
                
                if not image_paths:
                    return False, "PDF 转换为图片失败，未生成任何图片"
                
                # 使用视觉模型 API 处理
                return _ask_vision_model(question, image_paths)
                
            except Exception as e:
                return False, f"处理 PDF 文件时发生错误: {str(e)}"
            finally:
                # 清理临时文件
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    try:
                        os.unlink(temp_pdf_path)
                    except Exception:
                        pass
                if temp_image_dir and os.path.exists(temp_image_dir):
                    try:
                        shutil.rmtree(temp_image_dir)
                    except Exception:
                        pass

    # 非 PDF 或多个文件的情况，使用原有的 qwen-long 模型处理
    client = None
    uploaded = []
    try:
        client = _get_openai_client()

        for f in file_list:
            try:
                f.stream.seek(0)
            except Exception:
                # 流不支持 seek 时直接忽略
                pass

            file_obj = client.files.create(
                file=(f.filename, f.stream),
                purpose="file-extract",
            )
            uploaded.append(file_obj)

        fileids_str = ",".join([f"fileid://{obj.id}" for obj in uploaded])

        completion = client.chat.completions.create(
            model="qwen-long",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "system", "content": fileids_str},
                {"role": "user", "content": question},
            ],
            extra_body={"enable_search": False},
        )

        content = completion.choices[0].message.content
        return True, content

    except Exception as e:
        return False, str(e)

    finally:
        if client and uploaded:
            for obj in uploaded:
                try:
                    client.files.delete(obj.id)
                except Exception:
                    # 删除失败不阻断主流程
                    pass
