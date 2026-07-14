from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Headers de segurança para uma API JSON pura.

    CSP `default-src 'none'` é adequada porque esta aplicação nunca serve HTML
    (o frontend é uma SPA hospedada separadamente); `frame-ancestors 'none'` +
    X-Frame-Options bloqueiam clickjacking; nosniff impede MIME sniffing.
    HSTS só é emitido em produção — em desenvolvimento (http://localhost) o
    header seria ignorado ou atrapalharia.
    """

    def __init__(self, app: ASGIApp, *, enable_hsts: bool) -> None:
        self._app = app
        self._enable_hsts = enable_hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                ]
                if self._enable_hsts:
                    security_headers.append(
                        (b"strict-transport-security", b"max-age=63072000; includeSubDomains")
                    )
                headers.extend(security_headers)
            await send(message)

        await self._app(scope, receive, send_with_headers)
