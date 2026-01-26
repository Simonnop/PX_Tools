import requests

url = "http://127.0.0.1:10101/llm/ask_with_files"

with open("/Users/simonnop/Codebase/PX_Tools/鉴茶财经20260125春晚赛季拉开序幕【无评论】+xmtx93001.pdf", "rb") as f1:
    r = requests.post(
        url,
        data={"question": "提取图片中的文字内容"},
        files=[("files", f1)],
        timeout=600,
    )
print(r.json()["data"]["answer"])