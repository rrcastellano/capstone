from django import template
import locale

register = template.Library()

@register.filter
def brl(value, args=None):
    """
    Format number as currency/decimal based on active language.
    Usage: {{ value | brl }} or {{ value | brl:2 }} or {{ value | brl:"2,False" }}
    Arguments can be:
    - decimals (int, default 2)
    - with_prefix (bool, default True)
    Parsed from string/arg.
    """
    from django.utils.translation import get_language
    
    decimals = 2
    with_prefix = True
    
    # Parse args if provided as "decimals,with_prefix" or just decimals
    if args is not None:
        arg_list = [a.strip() for a in str(args).split(',')]
        if len(arg_list) > 0 and arg_list[0].isdigit():
            decimals = int(arg_list[0])
        if len(arg_list) > 1:
            with_prefix = arg_list[1].lower() not in ('false', '0', 'no')
            
    try:
        val = float(value)
    except (ValueError, TypeError):
        return "-"

    lang = get_language()
    
    # Check if Portuguese
    if lang and lang.lower().startswith('pt'):
        # Format as BR style: 1.234,56
        s_us = f"{val:,.{decimals}f}"
        s_fmt = s_us.replace(",", "X").replace(".", ",").replace("X", ".")
        symbol = "R$"
    else:
        # Format as US/Intl style: 1,234.56
        s_fmt = f"{val:,.{decimals}f}"
        symbol = "$"
    
    if with_prefix:
        return f"{symbol} {s_fmt}"
    return s_fmt

@register.filter
def date_fmt(value):
    """
    Formata data e hora com base no fuso horário ativo e no idioma atual.
    Converte instantes UTC para o horário local do usuário.
    """
    from django.utils import timezone
    from django.utils.translation import get_language
    from django.utils.dateparse import parse_datetime
    import datetime
    
    if not value:
        return ""

    dt = value
    if isinstance(dt, str):
        parsed = parse_datetime(dt)
        if parsed:
            dt = parsed
        else:
            try:
                dt = datetime.datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except Exception:
                return value

    if isinstance(dt, (datetime.datetime, datetime.date)):
        if isinstance(dt, datetime.datetime) and timezone.is_aware(dt):
            dt = timezone.localtime(dt)
    else:
        return str(value)
        
    lang = get_language()
    
    if lang and lang.lower().startswith('en'):
        fmt = "M/d/Y H:i"
    else:
        fmt = "d/M/Y H:i"
        
    from django.template.defaultfilters import date as django_date_filter
    return django_date_filter(dt, fmt)
