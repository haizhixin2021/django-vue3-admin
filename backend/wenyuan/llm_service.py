import json
import requests
from django.conf import settings


class SignListLLMParser:

    """
    调用dify发布的工作流解析处理签到人员列表
    """

    def __init__(self):
        self.api_key = getattr(settings, 'DIFY_API_KEY', '')
        self.api_url = getattr(settings, 'DIFY_API_URL', '')

    def _call_dify_workflow(self, checklist: str) -> str:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            "inputs": { "checklist": checklist },
            "response_mode": "blocking",
            "user": "django-vue3-admin-workflow"
        }
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            # 捕获 HTTP 错误（如 401, 500 等）
            print(f"HTTP 请求失败！状态码: {err.response.status_code}")
            print(f"服务器返回的错误信息: {err.response.text}")    
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None

        return resp.json()["data"]['outputs']['result']