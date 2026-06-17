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

    async def get_access_token(self) -> str:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": self.app_id,
                    "secret": self.app_secret,
                },
            )
        payload = response.json()
        if response.is_error or payload.get("errcode") or not payload.get("access_token"):
            raise WeChatAPIError("WeChat access token failed")
        return payload["access_token"]

    async def get_phone_number(self, code: str) -> dict:
        access_token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.weixin.qq.com/wxa/business/getuserphonenumber",
                params={"access_token": access_token},
                json={"code": code},
            )
        payload = response.json()
        if response.is_error or payload.get("errcode"):
            raise WeChatAPIError("WeChat phone binding failed")
        return payload.get("phone_info") or {}

    async def send_subscription_message(
        self,
        openid: str,
        template_id: str,
        page: str,
        data: dict,
    ) -> dict:
        access_token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.weixin.qq.com/cgi-bin/message/subscribe/send",
                params={"access_token": access_token},
                json={
                    "touser": openid,
                    "template_id": template_id,
                    "page": page,
                    "data": data,
                },
            )
        payload = response.json()
        if response.is_error or payload.get("errcode"):
            raise WeChatAPIError("WeChat subscription notification failed")
        return payload
