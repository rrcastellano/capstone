import zoneinfo
import urllib.parse
from django.utils import timezone

class TimezoneMiddleware:
    """
    Middleware para sincronizar o fuso horário ativo no Django com o fuso
    horário do navegador do usuário (enviado via cookie 'django_timezone' ou header 'X-Timezone').
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.headers.get('X-Timezone') or request.COOKIES.get('django_timezone')
        
        if tzname:
            try:
                # Decodifica caso venha codificado em URL (ex: America%2FSao_Paulo)
                tzname = urllib.parse.unquote(tzname).strip().strip('"\'')
                tz = zoneinfo.ZoneInfo(tzname)
                timezone.activate(tz)
            except Exception:
                try:
                    timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
                except Exception:
                    timezone.deactivate()
        else:
            # Fallback padrão: horário de Brasília
            try:
                timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
            except Exception:
                timezone.deactivate()

        return self.get_response(request)
