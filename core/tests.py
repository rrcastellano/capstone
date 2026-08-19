import json
import zoneinfo
import datetime
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Recharge, Settings
from core.forms import RechargeForm
from core.api_views import api_recharge_list, api_recharge_detail
from core.views import api_recharges_monthly, manage_recharges, validate_csv_and_parse
from core.templatetags.custom_filters import date_fmt
import io

class TimezoneMigrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.factory = RequestFactory()

    def test_recharge_model_utc_storage(self):
        """Verifica que o modelo salva e recupera datas em UTC timezone-aware."""
        dt_utc = datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc)
        recharge = Recharge.objects.create(
            user=self.user,
            data=dt_utc,
            kwh=25.5,
            custo=50.0,
            odometro=15000.0,
            bateria_antes=20,
            bateria_depois=80,
            tipo_recarga='AC'
        )
        saved = Recharge.objects.get(pk=recharge.pk)
        self.assertTrue(timezone.is_aware(saved.data))
        self.assertEqual(saved.data.astimezone(datetime.timezone.utc), dt_utc)

    def test_recharge_form_iso_utc_parsing(self):
        """Verifica que RechargeForm aceita ISO 8601 UTC ('...Z') e converte para UTC ciente."""
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        form_data = {
            'data': '2026-08-19T19:13:00.000Z',
            'kwh': 30.0,
            'custo': 60.0,
            'odometro': 12000.0,
            'bateria_antes': 10,
            'bateria_depois': 80,
            'tipo_recarga': 'AC',
        }
        form = RechargeForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned_dt = form.cleaned_data['data']
        self.assertTrue(timezone.is_aware(cleaned_dt))
        expected_utc = datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(cleaned_dt, expected_utc)

    def test_recharge_form_local_datetime_parsing(self):
        """Verifica que RechargeForm com string local (sem timezone) usa o fuso ativo e converte para UTC."""
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        form_data = {
            'data': '2026-08-19T16:13',
            'kwh': 30.0,
            'custo': 60.0,
            'odometro': 12000.0,
            'bateria_antes': 10,
            'bateria_depois': 80,
            'tipo_recarga': 'AC',
        }
        form = RechargeForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned_dt = form.cleaned_data['data']
        self.assertTrue(timezone.is_aware(cleaned_dt))
        # 16:13 em SP (UTC-3) deve ser 19:13 UTC
        expected_utc = datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(cleaned_dt, expected_utc)

    def test_api_recharge_create_and_list_utc(self):
        """Verifica que a API POST salva em UTC e GET retorna ISO 8601 UTC."""
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        payload = {
            "data": "2026-08-19T19:13:00.000Z",
            "kwh": 40.0,
            "custo": 80.0,
            "isento": False,
            "odometro": 20000.0,
            "bateria_antes": 20,
            "bateria_depois": 90,
            "tipo_recarga": "DC"
        }
        req_post = self.factory.post(
            '/api/recharges/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        req_post.user = self.user
        resp_post = api_recharge_list(req_post)
        self.assertEqual(resp_post.status_code, 200)
        res_data = json.loads(resp_post.content)
        recharge_id = res_data['id']

        recharge = Recharge.objects.get(pk=recharge_id)
        self.assertEqual(recharge.data, datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc))

        req_get = self.factory.get('/api/recharges/')
        req_get.user = self.user
        resp_get = api_recharge_list(req_get)
        self.assertEqual(resp_get.status_code, 200)
        items = json.loads(resp_get.content)
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]['data'].startswith('2026-08-19T19:13:00'))

    def test_api_recharge_detail_put(self):
        """Verifica atualização de data via PUT na API."""
        recharge = Recharge.objects.create(
            user=self.user,
            data=datetime.datetime(2026, 8, 19, 10, 0, 0, tzinfo=datetime.timezone.utc),
            kwh=10, custo=20, odometro=1000, bateria_antes=10, bateria_depois=50, tipo_recarga='AC'
        )
        payload = {"data": "2026-08-20T15:30:00.000Z", "kwh": 15}
        req_put = self.factory.put(
            f'/api/recharges/{recharge.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        req_put.user = self.user
        resp_put = api_recharge_detail(req_put, pk=recharge.id)
        self.assertEqual(resp_put.status_code, 200)

        recharge.refresh_from_db()
        self.assertEqual(recharge.data, datetime.datetime(2026, 8, 20, 15, 30, 0, tzinfo=datetime.timezone.utc))

    def test_monthly_grouping_across_midnight_boundary(self):
        """
        Teste crítico de borda:
        Recarga feita em 31 de Julho às 22:00 em Brasília (UTC-3).
        No banco Supabase / UTC é 01 de Agosto às 01:00 (2026-08-01T01:00:00Z).
        Para o usuário em Brasília, o agrupamento mensal DEVE ser '2026-07'.
        """
        dt_utc = datetime.datetime(2026, 8, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        Recharge.objects.create(
            user=self.user,
            data=dt_utc,
            kwh=20.0,
            custo=40.0,
            odometro=5000.0,
            bateria_antes=10,
            bateria_depois=70,
            tipo_recarga='AC'
        )

        # 1. Com fuso de São Paulo ativado -> agrupado em Julho (2026-07)
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        req = self.factory.get('/api/recharges/monthly/')
        req.user = self.user
        resp = api_recharges_monthly(req)
        data = json.loads(resp.content)
        self.assertEqual(data['labels'], ['2026-07'])

        # 2. Com fuso UTC ativado -> agrupado em Agosto (2026-08)
        timezone.activate(datetime.timezone.utc)
        req_utc = self.factory.get('/api/recharges/monthly/')
        req_utc.user = self.user
        resp_utc = api_recharges_monthly(req_utc)
        data_utc = json.loads(resp_utc.content)
        self.assertEqual(data_utc['labels'], ['2026-08'])

    def test_manage_recharges_date_filter_boundary(self):
        """
        Teste de filtro de data:
        Recarga feita às 22:00 de 31/07 no fuso de SP (01:00 UTC de 01/08).
        Filtrando de data_inicio=2026-07-31 a data_fim=2026-07-31 no fuso de SP DEVE encontrar a recarga.
        """
        dt_utc = datetime.datetime(2026, 8, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        Recharge.objects.create(
            user=self.user,
            data=dt_utc,
            kwh=20.0,
            custo=40.0,
            odometro=5000.0,
            bateria_antes=10,
            bateria_depois=70,
            tipo_recarga='AC'
        )

        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        self.client.force_login(self.user)
        resp = self.client.get('/history/?data_inicio=2026-07-31&data_fim=2026-07-31')
        self.assertEqual(resp.status_code, 200)
        recharges_ctx = resp.context['recharges']
        self.assertEqual(len(recharges_ctx), 1)

    def test_custom_filter_date_fmt(self):
        """Verifica que o filtro date_fmt converte o timestamp UTC para o fuso ativo."""
        dt_utc = datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc)
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        
        formatted = date_fmt(dt_utc)
        # Em São Paulo (UTC-3), 19:13 UTC é 16:13
        self.assertIn("16:13", formatted)

    def test_csv_import_with_iso_and_local(self):
        """Verifica que validate_csv_and_parse interpreta corretamente datas ISO UTC e locais."""
        timezone.activate(zoneinfo.ZoneInfo('America/Sao_Paulo'))
        csv_content = (
            "data,kwh,custo,isento,odometro,bateria_antes,bateria_depois,tipo_recarga\n"
            "2026-08-19T19:13:00Z,20,40,False,1000,20,80,AC\n"
            "2026-08-19 16:13,20,40,False,1050,20,80,AC\n"
        )
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        rows, errors = validate_csv_and_parse(file_obj)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(rows), 2)
        expected_utc = datetime.datetime(2026, 8, 19, 19, 13, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(rows[0]['data'], expected_utc)
        self.assertEqual(rows[1]['data'], expected_utc)

    def test_map_view_authenticated(self):
        """Verifica que usuário autenticado acessa a view de mapa com sucesso."""
        self.client.force_login(self.user)
        resp = self.client.get('/map/')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'core/map.html')

    def test_map_view_anonymous_redirect(self):
        """Verifica que usuário não autenticado é redirecionado para login."""
        resp = self.client.get('/map/')
        self.assertEqual(resp.status_code, 302)

    def test_api_recharges_coordinates(self):
        """Verifica que a API de recargas retorna latitude e longitude para plotagem no mapa."""
        Recharge.objects.create(
            user=self.user,
            data=datetime.datetime(2026, 8, 19, 15, 0, 0, tzinfo=datetime.timezone.utc),
            kwh=35.0,
            custo=70.0,
            odometro=8000.0,
            local='Posto Shell Eletroposto',
            bateria_antes=20,
            bateria_depois=80,
            tipo_recarga='DC',
            latitude=-23.55052,
            longitude=-46.63331
        )
        self.client.force_login(self.user)
        resp = self.client.get('/api/recharges/')
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        self.assertTrue(len(items) >= 1)
        found = [i for i in items if i['local'] == 'Posto Shell Eletroposto']
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]['latitude'], -23.55052)
        self.assertEqual(found[0]['longitude'], -46.63331)
        self.assertEqual(found[0]['tipo_recarga'], 'DC')

