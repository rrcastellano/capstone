import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Recharge, Settings

@csrf_exempt
def api_login(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get("username")
            password = data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({"status": "success", "message": "Logged in", "user_id": user.id})
            else:
                return JsonResponse({"status": "error", "message": "Invalid credentials"}, status=401)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def api_logout(request):
    logout(request)
    return JsonResponse({"status": "success", "message": "Logged out"})

@login_required
def api_settings(request):
    try:
        settings = Settings.objects.get(user=request.user)
        return JsonResponse({
            "limit_kwh": settings.limit_kwh,
            "limit_cost": settings.limit_cost
        })
    except Settings.DoesNotExist:
        return JsonResponse({"limit_kwh": 0, "limit_cost": 0})

@csrf_exempt
@login_required
def api_recharge_list(request):
    if request.method == "GET":
        recharges = Recharge.objects.filter(user=request.user).order_by('-data')
        data = []
        for r in recharges:
            data.append({
                "id": r.id,
                "data": r.data.isoformat(),
                "kwh": r.kwh,
                "custo": r.custo,
                "isento": r.isento,
                "odometro": r.odometro,
                "observacoes": r.observacoes,
                "local": r.local,
                "bateria_antes": r.bateria_antes,
                "bateria_depois": r.bateria_depois,
                "tipo_recarga": r.tipo_recarga,
                "latitude": r.latitude,
                "longitude": r.longitude,
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == "POST":
        try:
            body = json.loads(request.body)

            bat_antes_raw = body.get("bateria_antes")
            bat_depois_raw = body.get("bateria_depois")
            if bat_antes_raw is None or str(bat_antes_raw).strip() == "" or bat_depois_raw is None or str(bat_depois_raw).strip() == "":
                return JsonResponse({"status": "error", "message": "Informe o percentual da bateria antes e depois da recarga."}, status=400)
            
            try:
                bat_antes = int(float(str(bat_antes_raw).replace('%', '').strip()))
                bat_depois = int(float(str(bat_depois_raw).replace('%', '').strip()))
            except ValueError:
                return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)

            if bat_antes < 0 or bat_antes > 100 or bat_depois < 0 or bat_depois > 100:
                return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)

            if bat_depois < bat_antes:
                return JsonResponse({"status": "error", "message": "A bateria depois não pode ser menor que antes da recarga."}, status=400)

            tipo_recarga = (body.get("tipo_recarga") or "AC").strip().upper()
            if tipo_recarga not in ['AC', 'DC']:
                tipo_recarga = 'AC'

            recharge = Recharge.objects.create(
                user=request.user,
                data=body.get("data"),
                kwh=float(body.get("kwh", 0)),
                custo=float(body.get("custo", 0)),
                isento=body.get("isento", False),
                odometro=float(body.get("odometro", 0)),
                observacoes=body.get("observacoes", ""),
                local=body.get("local", ""),
                bateria_antes=bat_antes,
                bateria_depois=bat_depois,
                tipo_recarga=tipo_recarga,
                latitude=float(body.get("latitude")) if body.get("latitude") is not None else None,
                longitude=float(body.get("longitude")) if body.get("longitude") is not None else None
            )
            return JsonResponse({"status": "success", "id": recharge.id})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
@login_required
def api_recharge_detail(request, pk):
    try:
        recharge = Recharge.objects.get(pk=pk, user=request.user)
    except Recharge.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Recharge not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": recharge.id,
            "data": recharge.data.isoformat(),
            "kwh": recharge.kwh,
            "custo": recharge.custo,
            "isento": recharge.isento,
            "odometro": recharge.odometro,
            "observacoes": recharge.observacoes,
            "local": recharge.local,
            "bateria_antes": recharge.bateria_antes,
            "bateria_depois": recharge.bateria_depois,
            "tipo_recarga": recharge.tipo_recarga,
            "latitude": recharge.latitude,
            "longitude": recharge.longitude,
        })
    
    elif request.method == "PUT":
        try:
            body = json.loads(request.body)
            recharge.data = body.get("data", recharge.data)
            recharge.kwh = float(body.get("kwh", recharge.kwh))
            recharge.custo = float(body.get("custo", recharge.custo))
            recharge.isento = body.get("isento", recharge.isento)
            recharge.odometro = float(body.get("odometro", recharge.odometro))
            recharge.observacoes = body.get("observacoes", recharge.observacoes)
            recharge.local = body.get("local", recharge.local)
            
            bat_antes = recharge.bateria_antes
            bat_depois = recharge.bateria_depois

            if "bateria_antes" in body:
                bat_antes_raw = body.get("bateria_antes")
                if bat_antes_raw is None or str(bat_antes_raw).strip() == "":
                    return JsonResponse({"status": "error", "message": "Informe o percentual da bateria antes e depois da recarga."}, status=400)
                try:
                    bat_antes = int(float(str(bat_antes_raw).replace('%', '').strip()))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)

            if "bateria_depois" in body:
                bat_depois_raw = body.get("bateria_depois")
                if bat_depois_raw is None or str(bat_depois_raw).strip() == "":
                    return JsonResponse({"status": "error", "message": "Informe o percentual da bateria antes e depois da recarga."}, status=400)
                try:
                    bat_depois = int(float(str(bat_depois_raw).replace('%', '').strip()))
                except ValueError:
                    return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)

            if bat_antes is not None and (bat_antes < 0 or bat_antes > 100):
                return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)
            if bat_depois is not None and (bat_depois < 0 or bat_depois > 100):
                return JsonResponse({"status": "error", "message": "A bateria deve estar entre 0 e 100 %."}, status=400)
            if bat_antes is not None and bat_depois is not None and bat_depois < bat_antes:
                return JsonResponse({"status": "error", "message": "A bateria depois não pode ser menor que antes da recarga."}, status=400)

            recharge.bateria_antes = bat_antes
            recharge.bateria_depois = bat_depois

            if "tipo_recarga" in body:
                tipo = (body.get("tipo_recarga") or "").strip().upper()
                if tipo in ['AC', 'DC']:
                    recharge.tipo_recarga = tipo
            if "latitude" in body:
                recharge.latitude = float(body["latitude"]) if body["latitude"] is not None else None
            if "longitude" in body:
                recharge.longitude = float(body["longitude"]) if body["longitude"] is not None else None
            recharge.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    elif request.method == "DELETE":
        recharge.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
