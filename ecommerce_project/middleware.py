import inspect
from asgiref.sync import sync_to_async


class AsyncBridgeMiddleware:
    """Middleware that supports both async and sync downstream handlers.

    This middleware exposes an *async* `__call__` so under ASGI it will be
    awaited by Django. If the downstream `get_response` is async we `await`
    it directly; if it's sync we call it with `sync_to_async` so it runs in
    a threadpool and can be awaited safely. This avoids accidentally
    awaiting an `HttpResponse` instance (which caused the previous error).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._is_async = inspect.iscoroutinefunction(get_response)

    async def __call__(self, request):
        if self._is_async:
            return await self.get_response(request)
        return await sync_to_async(self.get_response, thread_sensitive=True)(request)
