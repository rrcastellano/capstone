(async function () {
  // Configurações globais do Chart.js para o tema escuro EVChargeLog_AOS
  if (window.Chart) {
    Chart.defaults.color = '#8b9481';
    Chart.defaults.borderColor = 'rgba(40, 48, 37, 0.5)';
    Chart.defaults.font.family = "'Inter', system-ui, -apple-system, sans-serif";
  }

  // Busca dados agregados por mês
  let apiData;
  try {
    // Use global variable defined in template
    const url = window.apiRechargesMonthlyUrl || "/api/recharges/monthly/";
    const res = await fetch(url);
    apiData = await res.json();
  } catch (err) {
    if (typeof LoadMonthlyDataErrorMessage !== 'undefined') console.error(LoadMonthlyDataErrorMessage, err);
    document.querySelectorAll('.chart-container').forEach(el => {
      const msg = typeof LoadDataUnavailableMessage !== 'undefined' ? LoadDataUnavailableMessage : 'Error loading data';
      el.innerHTML = `<div class="text-muted text-center pt-5">${msg}</div>`;
    });
    return;
  }

  // Se não houver dados
  if (!apiData || !apiData.labels || apiData.labels.length === 0) {
    document.querySelectorAll('.chart-container').forEach(el => {
      const msg = typeof NoDataToDisplayMessage !== 'undefined' ? NoDataToDisplayMessage : 'No data';
      el.innerHTML = `<div class="text-muted text-center pt-5">${msg}</div>`;
    });
    return;
  }

  // Converte "YYYY-MM" -> "MM/YYYY"
  const labels = apiData.labels.map(m => `${m.slice(5, 7)}/${m.slice(0, 4)}`);

  // Helpers de formatação
  const CurrencySymbolBRL = typeof window.CurrencySymbolBRL !== 'undefined' ? window.CurrencySymbolBRL : 'R$';
  const LocaleCodePtBR = typeof window.LocaleCodePtBR !== 'undefined' ? window.LocaleCodePtBR : 'pt-BR';

  const fmtBRL = v => CurrencySymbolBRL + ' ' + Number(v ?? 0).toLocaleString(LocaleCodePtBR, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fmtBRLInt = v => CurrencySymbolBRL + ' ' + Number(v ?? 0).toLocaleString(LocaleCodePtBR, { maximumFractionDigits: 0 });
  const fmtNum = v => Number(v ?? 0).toLocaleString(LocaleCodePtBR, { maximumFractionDigits: 2 });
  const fmtNumInt = v => Number(v ?? 0).toLocaleString(LocaleCodePtBR, { maximumFractionDigits: 0 });

  // Labels
  const LabelTotalCostBRL = typeof window.LabelTotalCostBRL !== 'undefined' ? window.LabelTotalCostBRL : 'Total Cost';
  const LabelPaidRechargesBRL = typeof window.LabelPaidRechargesBRL !== 'undefined' ? window.LabelPaidRechargesBRL : 'Paid Recharges';
  const LabelPercentPaidOverTotal = typeof window.LabelPercentPaidOverTotal !== 'undefined' ? window.LabelPercentPaidOverTotal : '% Paid';
  const LabelKWhInMonth = typeof window.LabelKWhInMonth !== 'undefined' ? window.LabelKWhInMonth : 'kWh/Month';
  const LabelKWhPer100Km = typeof window.LabelKWhPer100Km !== 'undefined' ? window.LabelKWhPer100Km : 'kWh/100km';
  const LabelKmInMonth = typeof window.LabelKmInMonth !== 'undefined' ? window.LabelKmInMonth : 'Km/Month';
  const LabelKm = typeof window.LabelKm !== 'undefined' ? window.LabelKm : 'Km';
  const LabelTotalSavingsBRL = typeof window.LabelTotalSavingsBRL !== 'undefined' ? window.LabelTotalSavingsBRL : 'Total Savings';
  const LabelPaidSavingsBRL = typeof window.LabelPaidSavingsBRL !== 'undefined' ? window.LabelPaidSavingsBRL : 'Savings (Paid)';

  // ============ Gráfico 1: Custos por Mês ============ //
  const elCustos = document.getElementById('chartCustos');
  if (elCustos) {
    new Chart(elCustos, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: LabelTotalCostBRL,
            data: apiData.custos.total,
            backgroundColor: 'rgba(77, 166, 255, 0.7)',
            borderColor: '#4da6ff',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'y'
          },
          {
            label: LabelPaidRechargesBRL,
            data: apiData.custos.pagas,
            backgroundColor: 'rgba(150, 226, 103, 0.7)',
            borderColor: '#96e267',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'y'
          },
          {
            type: 'line',
            label: LabelPercentPaidOverTotal,
            data: apiData.custos.percentual,
            borderColor: '#e0a845',
            backgroundColor: 'rgba(224, 168, 69, 0.2)',
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#e0a845',
            yAxisID: 'yPerc'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: {
            position: 'left',
            title: { display: true, text: CurrencySymbolBRL, color: '#8b9481' },
            ticks: { callback: value => fmtNumInt(value), color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' },
            beginAtZero: true
          },
          yPerc: {
            position: 'right',
            title: { display: false, text: '%' },
            ticks: { callback: value => value + '%', color: '#8b9481' },
            beginAtZero: true,
            suggestedMax: 100,
            grid: { drawOnChartArea: false }
          },
          x: {
            ticks: { color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' }
          }
        },
        plugins: {
          tooltip: {
            backgroundColor: '#10150d',
            borderColor: '#283025',
            borderWidth: 1,
            titleColor: '#e0e4d6',
            bodyColor: '#e0e4d6',
            callbacks: {
              label: ctx => {
                const dsLabel = ctx.dataset.label || '';
                const v = ctx.raw;
                return ctx.dataset.yAxisID === 'yPerc'
                  ? `${dsLabel}: ${v}%`
                  : `${dsLabel}: ${fmtBRL(v)}`;
              }
            }
          },
          legend: { position: 'bottom', labels: { color: '#e0e4d6', padding: 15 } }
        }
      }
    });
  }

  // ============ Gráfico 2: Consumo por Mês (kWh) Consumo / 100Km ============ //
  const elConsumo = document.getElementById('chartConsumo');
  if (elConsumo) {
    new Chart(elConsumo, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: LabelKWhInMonth,
            data: apiData.consumo,
            backgroundColor: 'rgba(150, 226, 103, 0.7)',
            borderColor: '#96e267',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'y'
          },
          {
            type: 'line',
            label: LabelKWhPer100Km,
            data: apiData.consumo_por_100km,
            borderColor: '#4da6ff',
            backgroundColor: 'rgba(77, 166, 255, 0.2)',
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#4da6ff',
            yAxisID: 'y2'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: {
            position: 'left',
            title: { display: true, text: 'kWh', color: '#8b9481' },
            ticks: { callback: value => fmtNum(value), color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' },
            beginAtZero: true
          },
          y2: {
            position: 'right',
            title: { display: true, text: LabelKWhPer100Km, color: '#8b9481' },
            ticks: { callback: value => fmtNum(value), color: '#8b9481' },
            beginAtZero: true,
            grid: { drawOnChartArea: false }
          },
          x: {
            ticks: { color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' }
          }
        },
        plugins: {
          tooltip: {
            backgroundColor: '#10150d',
            borderColor: '#283025',
            borderWidth: 1,
            titleColor: '#e0e4d6',
            bodyColor: '#e0e4d6',
            callbacks: {
              label: ctx => {
                const dsLabel = ctx.dataset.label || '';
                const v = ctx.raw;
                const unidade = ctx.dataset.yAxisID === 'y' ? 'kWh' : LabelKWhPer100Km;
                return `${dsLabel}: ${fmtNum(v)} ${unidade}`;
              }
            }
          },
          legend: { position: 'bottom', labels: { color: '#e0e4d6', padding: 15 } }
        }
      }
    });
  }

  // ============ Gráfico 3: Km Rodados por Mês ============ //
  const elKm = document.getElementById('chartKm');
  if (elKm) {
    new Chart(elKm, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: LabelKmInMonth,
          data: apiData.km,
          backgroundColor: 'rgba(139, 148, 129, 0.6)',
          borderColor: '#8b9481',
          borderWidth: 1,
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            title: { display: true, text: LabelKm, color: '#8b9481' },
            ticks: { callback: value => fmtNum(value), color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' },
            beginAtZero: true
          },
          x: {
            ticks: { color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' }
          }
        },
        plugins: {
          tooltip: {
            backgroundColor: '#10150d',
            borderColor: '#283025',
            borderWidth: 1,
            titleColor: '#e0e4d6',
            bodyColor: '#e0e4d6',
            callbacks: { label: c => `${c.dataset.label}: ${fmtNum(c.raw)} ${LabelKm}` }
          },
          legend: { position: 'bottom', labels: { color: '#e0e4d6', padding: 15 } }
        }
      }
    });
  }

  // ============ Gráfico 4: Valores Economizados por Mês ============ //
  const elEconomia = document.getElementById('chartEconomia');
  if (elEconomia) {
    new Chart(elEconomia, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: LabelTotalSavingsBRL,
            data: apiData.economia.total,
            backgroundColor: 'rgba(150, 226, 103, 0.8)',
            borderColor: '#96e267',
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: LabelPaidSavingsBRL,
            data: apiData.economia.pagas,
            backgroundColor: 'rgba(77, 166, 255, 0.6)',
            borderColor: '#4da6ff',
            borderWidth: 1,
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            title: { display: true, text: CurrencySymbolBRL, color: '#8b9481' },
            ticks: { callback: value => fmtNumInt(value), color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' },
            beginAtZero: true
          },
          x: {
            ticks: { color: '#8b9481' },
            grid: { color: 'rgba(40, 48, 37, 0.5)' }
          }
        },
        plugins: {
          tooltip: {
            backgroundColor: '#10150d',
            borderColor: '#283025',
            borderWidth: 1,
            titleColor: '#e0e4d6',
            bodyColor: '#e0e4d6',
            callbacks: { label: c => `${c.dataset.label}: ${fmtBRL(c.raw)}` }
          },
          legend: { position: 'bottom', labels: { color: '#e0e4d6', padding: 15 } }
        }
      }
    });
  }
})();
