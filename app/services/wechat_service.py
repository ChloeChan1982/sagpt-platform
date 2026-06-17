import httpx


class WeChatAPIError(Exception):
    """Raised for WeChat API failures without exposing secrets."""


class WeChatService:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
        payload = response.json()
        if response.is_error or payload.get("errcode"):
            raise WeChatAPIError("WeChat login failed")
        return payload
