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
    norm = unicodedata.normalize('NFKD', h).encode('ASCII', 'ignore').decode('utf-8').strip().lower()
    norm = norm.replace(" ", "_").replace("-", "_")
    if norm in ['bat_antes', 'bateria_inicial', 'soc_antes']:
        return 'bateria_antes'
    if norm in ['bat_depois', 'bateria_final', 'soc_depois']:
        return 'bateria_depois'
    if norm in ['tipo', 'tipo_de_recarga']:
        return 'tipo_recarga'
    if norm in ['lat']:
        return 'latitude'
    if norm in ['lng', 'lon']:
        return 'longitude'
    if norm in ['obs']:
        return 'observacoes'
    return norm

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
    required_headers = ['data', 'kwh', 'custo', 'isento', 'odometro', 'bateria_antes', 'bateria_depois', 'tipo_recarga']

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
            
            from django.utils import timezone
            from django.utils.dateparse import parse_datetime
            from datetime import datetime, timezone as dt_timezone
            
            parsed_dt = parse_datetime(data_str)
            if parsed_dt:
                dt = parsed_dt
            else:
                try:
                    dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        try:
                            dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                        except ValueError:
                            try:
                                dt = datetime.strptime(data_str, "%d/%m/%Y %H:%M")
                            except ValueError:
                                raise ValueError(_("Formato de data inválido (Use AAAA-MM-DD HH:MM)."))

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            dt = dt.astimezone(dt_timezone.utc)

            kwh = float((row.get('kwh') or "").replace(',', '.'))
            custo = float((row.get('custo') or "").replace(',', '.'))
            odometro = float((row.get('odometro') or "").replace(',', '.'))
            observacoes = (row.get('observacoes') or "").strip()
            local = (row.get('local') or "").strip()
            
            isento_raw = (row.get('isento') or "").strip().lower()
            isento = isento_raw in ["true", "1", "sim", "yes", "y"]
            if isento:
                custo = 0.0

            bat_antes_raw = (row.get('bateria_antes') or "").replace('%', '').strip()
            bat_depois_raw = (row.get('bateria_depois') or "").replace('%', '').strip()

            if not bat_antes_raw or not bat_depois_raw:
                raise ValueError(_("Informe o percentual da bateria antes e depois da recarga."))

            try:
                bateria_antes = int(float(bat_antes_raw))
                bateria_depois = int(float(bat_depois_raw))
            except ValueError:
                raise ValueError(_("A bateria deve estar entre 0 e 100 %."))

            if bateria_antes < 0 or bateria_antes > 100 or bateria_depois < 0 or bateria_depois > 100:
                raise ValueError(_("A bateria deve estar entre 0 e 100 %."))

            if bateria_depois < bateria_antes:
                raise ValueError(_("A bateria depois não pode ser menor que antes da recarga."))

            tipo_recarga = (row.get('tipo_recarga') or "").strip().upper()
            if not tipo_recarga:
                raise ValueError(_("Campo 'tipo_recarga' vazio."))
            if tipo_recarga not in ['AC', 'DC']:
                raise ValueError(_("Tipo de recarga inválido (deve ser AC ou DC)."))

            latitude = None
            try:
                lat_str = row.get('latitude') or row.get('lat')
                if lat_str and str(lat_str).strip():
                    latitude = float(str(lat_str).strip().replace(',', '.'))
            except Exception:
                pass

            longitude = None
            try:
                lon_str = row.get('longitude') or row.get('lon') or row.get('lng')
                if lon_str and str(lon_str).strip():
                    longitude = float(str(lon_str).strip().replace(',', '.'))
            except Exception:
                pass

            rows_validos.append({
                'data': dt,
                'kwh': kwh,
                'custo': custo,
                'odometro': odometro,
                'isento': isento,
                'observacoes': observacoes,
                'local': local,
                'bateria_antes': bateria_antes,
                'bateria_depois': bateria_depois,
                'tipo_recarga': tipo_recarga,
                'latitude': latitude,
                'longitude': longitude,
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
                is_exempt = bool(r.get('isento'))
                Recharge.objects.create(
                    user=request.user,
                    data=r['data'],
                    kwh=r['kwh'],
                    custo=0.0 if is_exempt else r['custo'],
                    isento=is_exempt,
                    odometro=r['odometro'],
                    observacoes=r.get('observacoes', ''),
                    local=r.get('local', ''),
                    bateria_antes=r.get('bateria_antes'),
                    bateria_depois=r.get('bateria_depois'),
                    tipo_recarga=r.get('tipo_recarga'),
                    latitude=r.get('latitude'),
                    longitude=r.get('longitude'),
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

    from django.utils import timezone

    if periodo_30d == '30d':
        data_30_dias_atras = timezone.now() - datetime.timedelta(days=30)
        recharge_list = recharge_list.filter(data__gte=data_30_dias_atras)
    else:
        current_tz = timezone.get_current_timezone()
        # Date filters
        if data_inicio:
            try:
                dt_ini_naive = datetime.datetime.strptime(data_inicio, "%Y-%m-%d")
                dt_ini = timezone.make_aware(dt_ini_naive, current_tz)
                recharge_list = recharge_list.filter(data__gte=dt_ini)
            except ValueError:
                pass
        
        if data_fim:
            try:
                # Inclui o dia final completo até 23:59:59.999999 no fuso local
                dt_fim_naive = datetime.datetime.strptime(data_fim, "%Y-%m-%d") + datetime.timedelta(days=1, microseconds=-1)
                dt_fim = timezone.make_aware(dt_fim_naive, current_tz)
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
        writer.writerow([
            'Data', 'Local', 'kWh', 'Custo', 'Odometro',
            'Bateria_Antes', 'Bateria_Depois', 'Tipo_Recarga',
            'Isento', 'Observacoes', 'Latitude', 'Longitude'
        ])

        for r in recharge_list:
            bat_antes = f"{r.bateria_antes}%" if r.bateria_antes is not None else ""
            bat_depois = f"{r.bateria_depois}%" if r.bateria_depois is not None else ""
            lat = r.latitude if r.latitude is not None else ""
            lng = r.longitude if r.longitude is not None else ""
            local_dt = timezone.localtime(r.data) if timezone.is_aware(r.data) else r.data

            writer.writerow([
                local_dt.strftime("%Y-%m-%d %H:%M"),
                r.local or "",
                r.kwh,
                r.custo,
                r.odometro,
                bat_antes,
                bat_depois,
                r.tipo_recarga or "",
                str(r.isento),
                r.observacoes or "",
                lat,
                lng
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
    user = request.user
    
    # --- Fetch Data ---
    recargas = Recharge.objects.filter(user=user).order_by('data')
    
    try:
        settings = user.settings
    except Settings.DoesNotExist:
        settings = None

    config = settings
    preco_kwh_medio = config.preco_kwh_medio if (config and config.preco_kwh_medio is not None) else 2.60
    
    # --- KPIs Calculation ---
    kwhs = [r.kwh for r in recargas]
    isentos = [r.isento for r in recargas]
    odometros = [r.odometro for r in recargas if r.odometro is not None]

    total_recargas = len(recargas)
    recargas_isentas_qtd = sum(1 for i in isentos if i)
    recargas_pagas_qtd = total_recargas - recargas_isentas_qtd
    
    if len(odometros) >= 2:
        total_km = odometros[-1] - odometros[0]
    elif len(odometros) == 1:
        total_km = odometros[0]
    else:
        total_km = 0.0
        
    kwh_isentas = sum(r.kwh for r in recargas if r.isento)
    consumo_total_kwh = sum(kwhs)
    
    # 1. Custo Pago (apenas recargas !isento)
    custo_pago = sum(r.custo for r in recargas if not r.isento)
    
    # 2. Economia por Isenção (kWh isentos * preco_kwh_medio)
    economia_isencao = kwh_isentas * preco_kwh_medio
    
    # 3. Custo Cheio / Teórico (custoPago + economiaIsencao)
    custo_cheio = custo_pago + economia_isencao
    
    consumo_por_100km = (consumo_total_kwh / total_km * 100) if total_km > 0 else 0
    custo_medio_kwh = (custo_pago / consumo_total_kwh) if consumo_total_kwh > 0 else 0
    custo_medio_km = (custo_pago / total_km) if total_km > 0 else 0

    # Config gasolina
    tem_config = config and config.preco_gasolina is not None and config.consumo_km_l and config.consumo_km_l > 0
    
    if tem_config:
        preco_gasolina = config.preco_gasolina
        consumo_km_l = config.consumo_km_l
        custo_gas_por_km = preco_gasolina / consumo_km_l
        custo_gas_total = (total_km / consumo_km_l) * preco_gasolina
        # Economia Real = custoGasolina - custoPago
        economia_real = custo_gas_total - custo_pago
        economia_real_por_km = economia_real / total_km if total_km > 0 else 0
        # Economia se Pagasse Tudo = custoGasolina - custoCheio
        economia_se_pagasse_tudo = custo_gas_total - custo_cheio
        economia_se_pagasse_tudo_por_km = economia_se_pagasse_tudo / total_km if total_km > 0 else 0
    else:
        custo_gas_por_km = None
        custo_gas_total = None
        economia_real = None
        economia_real_por_km = None
        economia_se_pagasse_tudo = None
        economia_se_pagasse_tudo_por_km = None

    kpis = {
        "recargas": total_recargas,
        "recargas_isentas_qtd": recargas_isentas_qtd,
        "recargas_pagas_qtd": recargas_pagas_qtd,
        "total_km": total_km,
        "consumo_total_kwh": consumo_total_kwh,
        "consumo_por_100km": consumo_por_100km,
        "custo_pago": custo_pago,
        "custo_pagas": custo_pago,
        "economia_isencao": economia_isencao,
        "custo_isentas": economia_isencao,
        "custo_cheio": custo_cheio,
        "custo_total": custo_cheio,
        "custo_medio_kwh": custo_medio_kwh,
        "custo_medio_km": custo_medio_km,
        "custo_gas_por_km": custo_gas_por_km,
        "custo_gas_total": custo_gas_total,
        "economia_real": economia_real,
        "economia_total": economia_real,
        "economia_real_por_km": economia_real_por_km,
        "economia_total_por_km": economia_real_por_km,
        "economia_se_pagasse_tudo": economia_se_pagasse_tudo,
        "economia_pagas": economia_se_pagasse_tudo,
        "economia_pagas_por_km": economia_se_pagasse_tudo_por_km,
        "economia_isencoes": economia_isencao,
        "preco_kwh_medio": preco_kwh_medio,
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
    from django.utils import timezone

    # Helpers
    def _to_month(dt):
        local_dt = timezone.localtime(dt) if timezone.is_aware(dt) else dt
        return local_dt.strftime("%Y-%m")

    user = request.user
    
    # Fetch Data
    recargas = Recharge.objects.filter(user=user).order_by('data')
    try:
        config = user.settings
    except Settings.DoesNotExist:
        config = None
        
    preco_gasolina = config.preco_gasolina if config else None
    consumo_km_l = config.consumo_km_l if config else None
    preco_kwh_medio = config.preco_kwh_medio if (config and config.preco_kwh_medio is not None) else 2.60
    tem_config = (preco_gasolina is not None) and (consumo_km_l is not None) and (consumo_km_l > 0)

    # Aggregation
    monthly = defaultdict(lambda: {
        "custo_pago": 0.0,
        "kwh_total": 0.0,
        "kwh_isentas": 0.0,
        "odometros": []
    })

    for r in recargas:
        mes = _to_month(r.data)
        monthly[mes]["kwh_total"] += r.kwh
        if r.isento:
            monthly[mes]["kwh_isentas"] += r.kwh
        else:
            monthly[mes]["custo_pago"] += r.custo
        if r.odometro is not None:
            monthly[mes]["odometros"].append(r.odometro)

    meses_ord = sorted(monthly.keys())
    
    # Response Arrays
    labels = []
    custos_cheio_list = []
    custos_pago_list = []
    custos_percentual_list = []
    consumos_list = []
    kms_list = []
    economias_real_list = []
    economias_se_pagasse_tudo_list = []
    economias_isencao_list = []
    consumo_por_100km_list = []

    for idx, mes in enumerate(meses_ord):
        data_mes = monthly[mes]
        labels.append(mes)
        
        cp = float(data_mes["custo_pago"])
        kwh_mes = round(float(data_mes["kwh_total"]), 2)
        kwh_isentas_mes = float(data_mes["kwh_isentas"])
        
        econ_isencao_mes = kwh_isentas_mes * preco_kwh_medio
        cc = cp + econ_isencao_mes
        
        custos_cheio_list.append(round(cc, 2))
        custos_pago_list.append(round(cp, 2))
        custos_percentual_list.append(round((cp / cc * 100) if cc > 0 else 0.0, 2))
        consumos_list.append(kwh_mes)
        economias_isencao_list.append(round(econ_isencao_mes, 2))
        
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
        else:
            km_mes = 0.0
            
        km_mes = max(km_mes, 0.0)
        kms_list.append(round(km_mes, 2))
        
        if km_mes > 0:
            consumo_por_100km_list.append(round((kwh_mes / km_mes) * 100, 2))
        else:
            consumo_por_100km_list.append(0)
            
        if tem_config:
            custo_gas_mes = (km_mes / consumo_km_l) * preco_gasolina
            economia_real_mes = custo_gas_mes - cp
            economia_se_pagasse_tudo_mes = custo_gas_mes - cc
        else:
            economia_real_mes = 0.0
            economia_se_pagasse_tudo_mes = 0.0
            
        economias_real_list.append(round(economia_real_mes, 2))
        economias_se_pagasse_tudo_list.append(round(economia_se_pagasse_tudo_mes, 2))
        
    # --- KPI Calculation ---
    kwhs = [r.kwh for r in recargas]
    isentos = [r.isento for r in recargas]
    all_odometros = [r.odometro for r in recargas if r.odometro is not None]

    total_recargas = len(recargas)
    recargas_isentas_qtd = sum(1 for i in isentos if i)
    recargas_pagas_qtd = total_recargas - recargas_isentas_qtd
    
    if len(all_odometros) >= 2:
        total_km = all_odometros[-1] - all_odometros[0]
    else:
        total_km = 0.0
        
    kwh_isentas = sum(r.kwh for r in recargas if r.isento)
    consumo_total_kwh = sum(kwhs)
    custo_pago = sum(r.custo for r in recargas if not r.isento)
    economia_isencao = kwh_isentas * preco_kwh_medio
    custo_cheio = custo_pago + economia_isencao
    
    consumo_por_100km = (consumo_total_kwh / total_km * 100) if total_km > 0 else 0
    custo_medio_kwh = (custo_pago / consumo_total_kwh) if consumo_total_kwh > 0 else 0
    custo_medio_km = (custo_pago / total_km) if total_km > 0 else 0

    # Config gasolina
    if tem_config:
        custo_gas_por_km = preco_gasolina / consumo_km_l
        custo_gas_total = (total_km / consumo_km_l) * preco_gasolina
        economia_real = custo_gas_total - custo_pago
        economia_real_por_km = economia_real / total_km if total_km > 0 else 0
        economia_se_pagasse_tudo = custo_gas_total - custo_cheio
        economia_se_pagasse_tudo_por_km = economia_se_pagasse_tudo / total_km if total_km > 0 else 0
    else:
        custo_gas_por_km = 0
        custo_gas_total = 0
        economia_real = 0
        economia_real_por_km = 0
        economia_se_pagasse_tudo = 0
        economia_se_pagasse_tudo_por_km = 0

    kpis = {
        "recargas": total_recargas,
        "recargas_isentas_qtd": recargas_isentas_qtd,
        "recargas_pagas_qtd": recargas_pagas_qtd,
        "total_km": total_km,
        "consumo_total_kwh": consumo_total_kwh,
        "consumo_por_100km": consumo_por_100km,
        "custo_pago": custo_pago,
        "custo_pagas": custo_pago,
        "economia_isencao": economia_isencao,
        "custo_isentas": economia_isencao,
        "custo_cheio": custo_cheio,
        "custo_total": custo_cheio,
        "custo_medio_kwh": custo_medio_kwh,
        "custo_medio_km": custo_medio_km,
        "custo_gas_por_km": custo_gas_por_km,
        "custo_gas_total": custo_gas_total,
        "economia_real": economia_real,
        "economia_total": economia_real,
        "economia_real_por_km": economia_real_por_km,
        "economia_total_por_km": economia_real_por_km,
        "economia_se_pagasse_tudo": economia_se_pagasse_tudo,
        "economia_pagas": economia_se_pagasse_tudo,
        "economia_pagas_por_km": economia_se_pagasse_tudo_por_km,
        "economia_isencoes": economia_isencao,
        "preco_kwh_medio": preco_kwh_medio,
    }

    return JsonResponse({
        "kpis": kpis,
        "labels": labels,
        "custos": {
            "total": custos_cheio_list,
            "pagas": custos_pago_list,
            "percentual": custos_percentual_list,
            "isencao": economias_isencao_list
        },
        "consumo": consumos_list,
        "km": kms_list,
        "economia": {
            "total": economias_real_list,
            "pagas": economias_se_pagasse_tudo_list,
            "isencao": economias_isencao_list
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


def delete_account(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            Recharge.objects.filter(user=user).delete()
            Settings.objects.filter(user=user).delete()
            logout(request)
            user.delete()
            messages.success(request, _('Sua conta e todos os seus dados foram excluídos permanentemente.'))
            return redirect('index')
        else:
            req_email = request.POST.get('email', '').strip()
            details = request.POST.get('details', '').strip()
            if req_email:
                ContactLog.objects.create(
                    name='Solicitação de Exclusão de Conta',
                    email=req_email,
                    message=f'Solicitação de exclusão para o e-mail: {req_email}. Detalhes: {details}',
                    status='Pendente'
                )
                messages.success(
                    request,
                    _('Sua solicitação de exclusão foi recebida com sucesso! Processaremos o pedido em até 48 horas.')
                )
            else:
                messages.error(request, _('Por favor, informe seu e-mail de cadastro.'))
            return redirect('delete_account')

    return render(request, 'core/delete_account.html')


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


@login_required
def map_view(request):
    return render(request, 'core/map.html')



