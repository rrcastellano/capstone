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
            })
        return JsonResponse(data, safe=False)
    
    elif request.method == "POST":
        try:
            body = json.loads(request.body)
            recharge = Recharge.objects.create(
                user=request.user,
                data=body.get("data"),
                kwh=float(body.get("kwh", 0)),
                custo=float(body.get("custo", 0)),
                isento=body.get("isento", False),
                odometro=float(body.get("odometro", 0)),
                observacoes=body.get("observacoes", ""),
                local=body.get("local", "")
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
            recharge.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    elif request.method == "DELETE":
        recharge.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
