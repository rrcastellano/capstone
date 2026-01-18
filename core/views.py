from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import RegisterForm, ContactForm, SettingsForm, RechargeForm
from .models import Recharge, Settings, ContactLog

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Cadastro realizado com sucesso!'))
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_log = form.save(commit=False)
            contact_log.status = 'Enviado' # Default status
            contact_log.save()
            messages.success(request, _('Mensagem enviada com sucesso!'))
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})

@login_required
def recharge(request):
    if request.method == 'POST':
        form = RechargeForm(request.POST)
        if form.is_valid():
            recharge = form.save(commit=False)
            recharge.user = request.user
            recharge.save()
            messages.success(request, _('Recarga registrada com sucesso!'))
            return redirect('dashboard')
    else:
        form = RechargeForm()
    return render(request, 'core/recharge.html', {'form': form})

# Helper for CSV
import csv
import io
import unicodedata

def normalize_header(h):
    if not h: return ""
    return unicodedata.normalize('NFKD', h).encode('ASCII', 'ignore').decode('utf-8').strip().lower()

def validate_csv_and_parse(file_storage):
    err_msgs = []
    rows_validos = []
    try:
        raw = file_storage.read()
    except Exception as e:
        return [], [_(f"Erro ao ler arquivo: {e}")]

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="ignore")
    
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    stream = io.StringIO(text, newline='')

    sample = text[:10000]
    delimiter = ','
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t', '|'])
        delimiter = dialect.delimiter
    except Exception:
        first_line = text.splitlines()[0] if text.splitlines() else ""
        if ';' in first_line and ',' not in first_line:
            delimiter = ';'
        elif '\t' in first_line:
            delimiter = '\t'

    try:
        reader = csv.DictReader(stream, delimiter=delimiter)
    except Exception as e:
        return [], [_(f"Erro ao preparar leitor CSV: {e}")]

    if not reader.fieldnames:
        return [], [_("Arquivo CSV sem cabeçalho.")]

    # Normalize headers behavior: Remove accents, lowercase
    reader.fieldnames = [normalize_header(h) for h in reader.fieldnames]
    required_headers = ['data', 'kwh', 'custo', 'isento', 'odometro']
    # observacoes is optional

    missing = [h for h in required_headers if h not in reader.fieldnames]
    if missing:
        msg = _("Cabeçalhos inválidos. Esperados: %(expected)s. Ausentes: %(missing)s") % {
            'expected': ", ".join(required_headers),
            'missing': ", ".join(missing)
        }
        return [], [msg]

    line_num = 1
    for row in reader:
        line_num += 1
        # Skip empty lines
        if all((row.get(h) is None or str(row.get(h)).strip() == "") for h in required_headers):
            continue
            
        try:
            data_str = (row.get('data') or "").strip()
            if not data_str:
                raise ValueError(_("Campo 'data' vazio."))
            
            from datetime import datetime
            try:
                # Attempt ISO
                dt = datetime.fromisoformat(data_str.replace(' ', 'T'))
            except ValueError:
                raise ValueError(_("Formato de data inválido (Use AAAA-MM-DD HH:MM)."))

            kwh = float((row.get('kwh') or "").replace(',', '.'))
            custo = float((row.get('custo') or "").replace(',', '.'))
            odometro = float((row.get('odometro') or "").replace(',', '.'))
            observacoes = (row.get('observacoes') or "").strip()
            local = (row.get('local') or "").strip()
            
            isento_raw = (row.get('isento') or "").strip().lower()
            isento = isento_raw in ["true", "1", "sim", "yes", "y"]

            rows_validos.append({
                'data': dt,
                'kwh': kwh,
                'custo': custo,
                'odometro': odometro,
                'isento': isento,
                'observacoes': observacoes,
                'local': local,
            })
        except ValueError as ve:
            err_msgs.append(_(f"Linha {line_num}: {ve}"))
        except Exception as e:
            err_msgs.append(_(f"Linha {line_num}: erro inesperado: {e}"))

    if not rows_validos and not err_msgs:
        err_msgs.append(_("Nenhuma linha válida encontrada no CSV."))
        
    return rows_validos, err_msgs

@login_required
def bulk_recharge(request):
    if request.method == 'POST':
        # Simple file handling without full form for now or use valid form if one exists
        # Flask used BulkRechargeForm with FileField. 
        # We can just check request.FILES['file']
        if 'file' not in request.FILES:
             messages.error(request, _('Nenhum arquivo enviado.'))
             return redirect('bulk_recharge')
             
        file = request.FILES['file']
        rows, errors = validate_csv_and_parse(file)
        
        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect('bulk_recharge')
            
        count = 0
        for r in rows:
            try:
                Recharge.objects.create(
                    user=request.user,
                    data=r['data'],
                    kwh=r['kwh'],
                    custo=r['custo'],
                    isento=r['isento'],
                    odometro=r['odometro'],
                    observacoes=r.get('observacoes', ''),
                    local=r.get('local', '')
                )
                count += 1
            except Exception as e:
                messages.warning(request, _(f"Erro ao salvar linha: {e}"))
        
        messages.success(request, _(f"Importação concluída: {count} recargas adicionadas."))
        return redirect('dashboard')

    return render(request, 'core/bulk_recharge.html')

@login_required
def manage_recharges(request):
    import datetime
    from django.db.models import Q

    # Filters
    local_query = request.GET.get('local', '')
    obs_query = request.GET.get('observacoes', '')
    isento_query = request.GET.get('isento', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    periodo_30d = request.GET.get('periodo', '')

    recharge_list = Recharge.objects.filter(user=request.user)

    if periodo_30d == '30d':
        data_30_dias_atras = datetime.datetime.now() - datetime.timedelta(days=30)
        recharge_list = recharge_list.filter(data__gte=data_30_dias_atras)
    else:
        # Date filters
        if data_inicio:
            try:
                dt_ini = datetime.datetime.strptime(data_inicio, "%Y-%m-%d")
                recharge_list = recharge_list.filter(data__gte=dt_ini)
            except ValueError:
                pass
        
        if data_fim:
            try:
                # Add 23:59:59 to include the end date fully
                dt_fim = datetime.datetime.strptime(data_fim, "%Y-%m-%d") + datetime.timedelta(days=1, microseconds=-1)
                recharge_list = recharge_list.filter(data__lte=dt_fim)
            except ValueError:
                pass

    if local_query:
        recharge_list = recharge_list.filter(local__icontains=local_query)
    
    if obs_query:
        recharge_list = recharge_list.filter(observacoes__icontains=obs_query)
    
    if isento_query:
        if isento_query == 'True':
             recharge_list = recharge_list.filter(isento=True)
        elif isento_query == 'False':
             recharge_list = recharge_list.filter(isento=False)

    recharge_list = recharge_list.order_by('-data')

    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(recharge_list, 20)
    page = request.GET.get('page')
    try:
        recharges = paginator.page(page)
    except PageNotAnInteger:
        recharges = paginator.page(1)
    except EmptyPage:
        recharges = paginator.page(paginator.num_pages)

    # Export CSV
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse

        has_filters = any([local_query, obs_query, isento_query, data_inicio, data_fim, periodo_30d])
        filename = "recharge_export_filtered.csv" if has_filters else "recharge_export_complete.csv"

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Data', 'Local', 'kWh', 'Custo', 'Odometro', 'Isento', 'Observacoes'])

        for r in recharge_list:
            writer.writerow([
                r.data.strftime("%Y-%m-%d %H:%M"),
                r.local or "",
                r.kwh,
                r.custo,
                r.odometro,
                str(r.isento),
                r.observacoes or ""
            ])
        return response

    isento_ctx = None
    if isento_query == 'True':
        isento_ctx = True
    elif isento_query == 'False':
        isento_ctx = False

    context = {
        'recharges': recharges,
        'filters': {
            'local': local_query,
            'observacoes': obs_query,
            'isento': isento_ctx,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'periodo': periodo_30d,
        }
    }
    return render(request, 'core/manage_recharges.html', context)

@login_required
def edit_recharge(request, pk):
    recharge = Recharge.objects.filter(user=request.user, pk=pk).first()
    if not recharge:
        messages.error(request, _('Recarga não encontrada.'))
        return redirect('manage_recharges')
        
    if request.method == 'POST':
        form = RechargeForm(request.POST, instance=recharge)
        if form.is_valid():
            form.save()
            messages.success(request, _('Recarga atualizada com sucesso!'))
            return redirect('manage_recharges')
    else:
        form = RechargeForm(instance=recharge)
    
    # Reuse recharge.html as it is a standard form
    return render(request, 'core/recharge.html', {'form': form, 'is_edit': True})

@login_required
def delete_recharge(request, pk):
    recharge = Recharge.objects.filter(user=request.user, pk=pk).first()
    if recharge:
        recharge.delete()
        messages.success(request, _('Recarga removida.'))
    return redirect('manage_recharges')


@login_required
def dashboard(request):
    from django.db.models import Sum, Min, Max
    from collections import defaultdict
    import datetime

    user = request.user
    
    # --- Fetch Data ---
    recargas = Recharge.objects.filter(user=user).order_by('data')
    
    try:
        settings = user.settings
    except Settings.DoesNotExist:
        settings = None

    config = settings
    
    # --- KPIs Calculation ---
    kwhs = [r.kwh for r in recargas]
    custos = [r.custo for r in recargas]
    isentos = [r.isento for r in recargas]
    odometros = [r.odometro for r in recargas if r.odometro is not None]

    total_recargas = len(recargas)
    recargas_isentas_qtd = sum(1 for i in isentos if i)
    recargas_pagas_qtd = total_recargas - recargas_isentas_qtd
    
    if len(odometros) >= 2:
        total_km = odometros[-1] - odometros[0]
    elif len(odometros) == 1:
        total_km = odometros[0] # Fallback logic from Flask? Flask logic: odometros[0] if odometros else 0
    else:
        total_km = 0.0
        
    custo_total = sum(custos)
    custo_isentas = sum(c for c, i in zip(custos, isentos) if i)
    custo_pagas = sum(c for c, i in zip(custos, isentos) if not i)
    consumo_total_kwh = sum(kwhs)
    
    consumo_por_100km = (consumo_total_kwh / total_km * 100) if total_km > 0 else 0
    custo_medio_kwh = (custo_total / consumo_total_kwh) if consumo_total_kwh > 0 else 0
    custo_medio_km = (custo_total / total_km) if total_km > 0 else 0

    # Config gasolina
    tem_config = config and config.preco_gasolina is not None and config.consumo_km_l and config.consumo_km_l > 0
    
    if tem_config:
        preco_gasolina = config.preco_gasolina
        consumo_km_l = config.consumo_km_l
        custo_gas_por_km = preco_gasolina / consumo_km_l
        custo_gas_total = (total_km / consumo_km_l) * preco_gasolina
        economia_total = custo_gas_total - custo_total
        economia_total_por_km = economia_total / total_km if total_km > 0 else 0
        economia_pagas = custo_gas_total - custo_pagas
        economia_pagas_por_km = economia_pagas / total_km if total_km > 0 else 0
    else:
        custo_gas_por_km = None
        custo_gas_total = None
        economia_total = None
        economia_total_por_km = None
        economia_pagas = None
        economia_pagas_por_km = None

    kpis = {
        "recargas": total_recargas,
        "recargas_isentas_qtd": recargas_isentas_qtd,
        "recargas_pagas_qtd": recargas_pagas_qtd,
        "total_km": total_km,
        "consumo_total_kwh": consumo_total_kwh,
        "consumo_por_100km": consumo_por_100km,
        "custo_total": custo_total,
        "custo_isentas": custo_isentas,
        "custo_pagas": custo_pagas,
        "custo_medio_kwh": custo_medio_kwh,
        "custo_medio_km": custo_medio_km,
        "custo_gas_por_km": custo_gas_por_km,
        "custo_gas_total": custo_gas_total,
        "economia_total": economia_total,
        "economia_total_por_km": economia_total_por_km,
        "economia_pagas": economia_pagas,
        "economia_pagas_por_km": economia_pagas_por_km,
    }

    context = {
        'kpis': kpis,
        'has_complete_config': tem_config
    }
    return render(request, 'core/dashboard.html', context)
    
@login_required
def api_recharges_monthly(request):
    from django.http import JsonResponse
    from collections import defaultdict
    # Helpers
    def _to_month(dt):
        return dt.strftime("%Y-%m")

    user = request.user
    
    # Fetch Data
    recargas = Recharge.objects.filter(user=user).order_by('data')
    try:
        config = user.settings
    except Settings.DoesNotExist:
        config = None
        
    preco_gasolina = config.preco_gasolina if config else None
    consumo_km_l = config.consumo_km_l if config else None
    tem_config = (preco_gasolina is not None) and (consumo_km_l is not None) and (consumo_km_l > 0)

    # Aggregation
    monthly = defaultdict(lambda: {
        "custo_total": 0.0,
        "custo_pagamento": 0.0,
        "kwh": 0.0,
        "odometros": []
    })

    for r in recargas:
        mes = _to_month(r.data)
        monthly[mes]["custo_total"] += r.custo
        monthly[mes]["kwh"] += r.kwh
        if r.odometro is not None:
            monthly[mes]["odometros"].append(r.odometro)
        if not r.isento:
            monthly[mes]["custo_pagamento"] += r.custo

    meses_ord = sorted(monthly.keys())
    
    # Response Arrays
    labels = []
    custos_total = []
    custos_pagamento = []
    custos_percentual = []
    consumos = []
    kms = []
    economias_total = []
    economias_pagamento = []
    consumo_por_100km_list = []

    for idx, mes in enumerate(meses_ord):
        data_mes = monthly[mes]
        labels.append(mes)
        
        ct = float(data_mes["custo_total"])
        cp = float(data_mes["custo_pagamento"])
        custos_total.append(round(ct, 2))
        custos_pagamento.append(round(cp, 2))
        custos_percentual.append(round((cp / ct * 100) if ct > 0 else 0.0, 2))
        
        consumo_mes = round(float(data_mes["kwh"]), 2)
        consumos.append(consumo_mes)
        
        odos = sorted(data_mes["odometros"])
        if len(odos) >= 2:
            km_mes = odos[-1] - odos[0]
        elif len(odos) == 1:
            if idx > 0:
                prev_mes = meses_ord[idx-1]
                prev_odos = sorted(monthly[prev_mes]["odometros"])
                prev_last = prev_odos[-1] if prev_odos else 0.0
                km_mes = odos[0] - prev_last
            else:
                km_mes = 0.0
                # Could argue odos[0] if it's the very first month, but logic says diff.
                # Use 0.0 to be safe
        else:
            km_mes = 0.0
            
        # Prevent negative km if data is weird
        km_mes = max(km_mes, 0.0)
        kms.append(round(km_mes, 2))
        
        if km_mes > 0:
            consumo_por_100km_list.append(round((consumo_mes / km_mes) * 100, 2))
        else:
            consumo_por_100km_list.append(0)
            
        if tem_config:
            custo_gas_mes = (km_mes / consumo_km_l) * preco_gasolina
            economia_total_mes = custo_gas_mes - ct
            economia_pagamento_mes = custo_gas_mes - cp
        else:
            economia_total_mes = 0.0
            economia_pagamento_mes = 0.0
            
        economias_total.append(round(economia_total_mes, 2))
        economias_pagamento.append(round(economia_pagamento_mes, 2))
        
    # --- KPI Calculation (Copied from dashboard view) ---
    kwhs = [r.kwh for r in recargas]
    custos = [r.custo for r in recargas]
    isentos = [r.isento for r in recargas]
    # We need odometros for total_km. Note: recargas is ordered by data.
    # The monthly loop below handles granular data, but for total KPIs we need overall range.
    all_odometros = [r.odometro for r in recargas if r.odometro is not None]

    total_recargas = len(recargas)
    recargas_isentas_qtd = sum(1 for i in isentos if i)
    recargas_pagas_qtd = total_recargas - recargas_isentas_qtd
    
    if len(all_odometros) >= 2:
        total_km = all_odometros[-1] - all_odometros[0]
    elif len(all_odometros) == 1:
         # Fallback logic if needed, but safe to say 0 or just the value? 
         # Dashboard view logic seems to imply 0 if only 1 reading usually, or specific logic.
         total_km = 0.0 
    else:
        total_km = 0.0
        
    custo_total = sum(custos)
    custo_isentas = sum(c for c, i in zip(custos, isentos) if i)
    custo_pagas = sum(c for c, i in zip(custos, isentos) if not i)
    consumo_total_kwh = sum(kwhs)
    
    consumo_por_100km = (consumo_total_kwh / total_km * 100) if total_km > 0 else 0
    custo_medio_kwh = (custo_total / consumo_total_kwh) if consumo_total_kwh > 0 else 0
    custo_medio_km = (custo_total / total_km) if total_km > 0 else 0

    # Config gasolina
    if tem_config:
        custo_gas_por_km = preco_gasolina / consumo_km_l
        custo_gas_total = (total_km / consumo_km_l) * preco_gasolina
        economia_total = custo_gas_total - custo_total
        economia_total_por_km = economia_total / total_km if total_km > 0 else 0
        economia_pagas = custo_gas_total - custo_pagas
        economia_pagas_por_km = economia_pagas / total_km if total_km > 0 else 0
    else:
        custo_gas_por_km = 0
        custo_gas_total = 0
        economia_total = 0
        economia_total_por_km = 0
        economia_pagas = 0
        economia_pagas_por_km = 0

    kpis = {
        "recargas": total_recargas,
        "recargas_isentas_qtd": recargas_isentas_qtd,
        "recargas_pagas_qtd": recargas_pagas_qtd,
        "total_km": total_km,
        "consumo_total_kwh": consumo_total_kwh,
        "consumo_por_100km": consumo_por_100km,
        "custo_total": custo_total,
        "custo_isentas": custo_isentas,
        "custo_pagas": custo_pagas,
        "custo_medio_kwh": custo_medio_kwh,
        "custo_medio_km": custo_medio_km,
        "custo_gas_por_km": custo_gas_por_km,
        "custo_gas_total": custo_gas_total,
        "economia_total": economia_total,
        "economia_total_por_km": economia_total_por_km,
        "economia_pagas": economia_pagas,
        "economia_pagas_por_km": economia_pagas_por_km,
    }

    return JsonResponse({
        "kpis": kpis,
        "labels": labels,
        "custos": {
            "total": custos_total,
            "pagas": custos_pagamento,
            "percentual": custos_percentual
        },
        "consumo": consumos,
        "km": kms,
        "economia": {
            "total": economias_total,
            "pagas": economias_pagamento
        },
        "consumo_por_100km": consumo_por_100km_list
    })

@login_required
def delete_all_recharges(request):
    if request.method == 'POST':
        count, ignored = Recharge.objects.filter(user=request.user).delete()
        messages.success(request, _(f'Todas as {count} recargas foram excluídas.'))
    return redirect('settings')

@login_required
def settings_view(request):
    try:
        settings = request.user.settings
    except Settings.DoesNotExist:
        settings = None

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save(commit=False)
            settings.user = request.user
            settings.save()
            messages.success(request, _('Configurações salvas!'))
            return redirect('settings')
    else:
        form = SettingsForm(instance=settings)
    return render(request, 'core/account.html', {'form': form})

