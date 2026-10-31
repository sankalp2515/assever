"""Bounded HTTP-body capture before JSON parsing, including chunked uploads."""

from starlette.responses import JSONResponse


class RequestLimit:
    def __init__(self, app, limit=65536, prefix=None):
        self.app, self.limit, self.prefix = app, limit, prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] in ("GET", "HEAD", "OPTIONS"):
            return await self.app(scope, receive, send)
        if self.prefix and not scope.get("path", "").startswith(self.prefix):
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            body = message.get("body", b"")
            size += len(body)
            if size > self.limit:
                response = JSONResponse(
                    {
                        "code": "REQUEST_TOO_LARGE",
                        "message": "Request exceeds 64 KiB.",
                        "correlation_id": scope.get("state", {}).get("correlation_id", ""),
                        "retryable": False,
                    },
                    status_code=413,
                    headers={"Connection": "close"},
                )
                return await response(scope, receive, send)
            chunks.append(body)
            if not message.get("more_body", False):
                break
        content = b"".join(chunks)
        first = True

        async def replay():
            nonlocal first
            if first:
                first = False
                return {"type": "http.request", "body": content, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
