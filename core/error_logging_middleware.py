import logging
import traceback
import sys

logger = logging.getLogger('django.request')

class ExceptionLoggingMiddleware:
    """
    Middleware para capturar e imprimir no stdout/stderr o traceback completo
    de qualquer exceção não tratada (erro 500) antes de retornar a resposta de erro.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        tb_str = traceback.format_exc()
        user_str = str(getattr(request, 'user', 'Anonymous'))
        print(f"\n==================== [DJANGO 500 ERROR] ====================", file=sys.stderr)
        print(f"Path: {request.path}", file=sys.stderr)
        print(f"Method: {request.method}", file=sys.stderr)
        print(f"User: {user_str}", file=sys.stderr)
        print(f"Exception Type: {type(exception).__name__}", file=sys.stderr)
        print(f"Exception Message: {exception}", file=sys.stderr)
        print("Traceback:", file=sys.stderr)
        print(tb_str, file=sys.stderr)
        print(f"============================================================\n", file=sys.stderr)
        logger.error(
            f"500 Internal Server Error at {request.path} (User: {user_str}): {exception}\n{tb_str}"
        )
        return None
