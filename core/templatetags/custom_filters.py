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
    Format date based on active language.
    EN: mmm/dd/yyyy (e.g. Jan/10/2026) -> Django: M/d/Y (Wait, user said mmm/dd. 'M' is Jan. 'd' is 10.)
    Others: dd/mmm/yyyy (e.g. 10/Jan/2026) -> Django: d/M/Y
    Time is not requested to change, but usually kept. User only specified date format.
    Let's keep time if useful, or just return date string? 
    Context shows |date:"d/m/Y H:i". User asked "formato de data... mmm/dd/yyyy". 
    I will include H:i as well to maintain existing utility if desired, or return just the date string part?
    The user request specifically dictates the date format pattern. I will append the time in a standard format or just simple date. 
    The current "d/m/Y H:i" implies they want time. I'll make the filter return the formatted string suitable for `date` filter or format it directly.
    Best to format directly.
    """
    from django.utils import timezone
    from django.utils.translation import get_language
    
    if not value:
        return ""
        
    lang = get_language()
    
    # User requested:
    # English: mmm/dd/yyyy (e.g. Jan/10/2026) -> Django format chars: 'M/d/Y'
    # Other: dd/mmm/yyyy (e.g. 10/Jan/2026) -> Django format chars: 'd/M/Y'
    
    # Note: 'M' is "Jan", "Feb". 'b' is 'jan', 'feb'. 
    # Validating "mmm": likely 3-letter month. 'M' works.
    
    if lang and lang.lower().startswith('en'):
        fmt = "M/d/Y H:i"
    else:
        fmt = "d/M/Y H:i"
        
    # We can use Django's date format function
    from django.template.defaultfilters import date as django_date_filter
    return django_date_filter(value, fmt)
