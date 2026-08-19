/**
 * EVChargeLog - Mapa de Estações de Recarga
 * Leaflet Dark Matter + Agrupamento por Coordenadas + Filtros em Tempo Real
 */
(function () {
  'use strict';

  let map;
  let allStations = [];
  let filteredStations = [];
  let markersLayer;
  let userLocationMarker = null;
  let selectedStationKey = null;

  // Estado dos Filtros
  let searchQuery = '';
  let filterDcOnly = false;
  let filterFreeOnly = false;

  const i18n = window.I18nMap || {
    loadingStations: 'Carregando estações...',
    locationsFound: 'locais encontrados',
    locationFound: 'local encontrado',
    noLocationsFound: 'Nenhum local encontrado',
    noLocationCoordinates: 'Nenhuma recarga com coordenadas GPS encontrada.',
    currencySymbol: 'R$',
    exemptLabel: 'Isenta',
    errorLoadingData: 'Erro ao carregar dados do mapa.',
    gpsError: 'Não foi possível obter sua localização GPS.',
    gpsSearching: 'Obtendo sua localização...'
  };

  /**
   * Inicializa o mapa Leaflet com o tema CartoDB Dark Matter
   */
  function initMap() {
    const mapEl = document.getElementById('recharges-map');
    if (!mapEl) return;

    // Centro inicial no Brasil / América Latina
    map = L.map('recharges-map', {
      center: [-15.7801, -47.9292],
      zoom: 4,
      zoomControl: false // reposicionaremos ou usaremos controles customizados
    });

    // Adiciona zoom control no canto inferior direito
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Tile Layer CartoDB Dark Matter
    L.tileLayer('https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>'
    }).addTo(map);

    markersLayer = L.featureGroup().addTo(map);

    // Deseleciona ao clicar no mapa
    map.on('click', function (e) {
      if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.closest('.custom-station-pin')) {
        return; // clique no marcador
      }
      deselectStation();
    });
  }

  /**
   * Agrupa registros individuais de recarga por coordenadas (5 casas decimais)
   */
  function groupRechargesByLocation(recharges) {
    const groups = {};

    recharges.forEach((r) => {
      if (r.latitude === null || r.latitude === undefined || r.longitude === null || r.longitude === undefined) {
        return;
      }
      const lat = parseFloat(r.latitude);
      const lng = parseFloat(r.longitude);
      if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) {
        return;
      }

      const key = `${lat.toFixed(5)},${lng.toFixed(5)}`;

      if (!groups[key]) {
        groups[key] = {
          key: key,
          lat: lat,
          lng: lng,
          local: (r.local || '').trim() || 'Estação de Recarga',
          count: 0,
          totalKwh: 0,
          totalCusto: 0,
          exemptCount: 0,
          hasDc: false,
          latestDate: null,
          recharges: []
        };
      }

      const g = groups[key];
      g.count += 1;
      g.totalKwh += parseFloat(r.kwh || 0);
      g.totalCusto += parseFloat(r.custo || 0);
      if (r.isento) g.exemptCount += 1;
      if (r.tipo_recarga && String(r.tipo_recarga).toUpperCase() === 'DC') g.hasDc = true;

      if (r.local && r.local.trim()) {
        g.local = r.local.trim();
      }

      // Atualiza data mais recente
      if (r.data) {
        if (!g.latestDate || new Date(r.data) > new Date(g.latestDate)) {
          g.latestDate = r.data;
        }
      }

      g.recharges.push(r);
    });

    return Object.values(groups).map((g) => {
      g.allExempt = g.exemptCount === g.count;
      return g;
    });
  }

  /**
   * Cria o Marker DivIcon customizado para a estação
   */
  function createStationMarker(station) {
    const isExempt = station.allExempt;
    const markerClass = isExempt ? 'pin-exempt' : 'pin-paid';
    const isSelected = selectedStationKey === station.key;
    const selectedClass = isSelected ? 'pin-selected' : '';
    const dcBadge = station.hasDc ? '<span class="pin-dc-icon"><i class="fas fa-bolt"></i></span>' : '';

    const html = `
      <div class="custom-station-pin ${markerClass} ${selectedClass}" id="pin-${station.key.replace(/[^a-zA-Z0-9]/g, '_')}">
        <div class="pin-halo"></div>
        <div class="pin-circle">
          <span class="pin-count">${station.count}</span>
          ${dcBadge}
        </div>
      </div>
    `;

    const icon = L.divIcon({
      className: 'station-div-icon-container',
      html: html,
      iconSize: [38, 38],
      iconAnchor: [19, 19]
    });

    const marker = L.marker([station.lat, station.lng], {
      icon: icon,
      title: station.local,
      riseOnHover: true
    });

    marker.on('click', (e) => {
      L.DomEvent.stopPropagation(e);
      selectStation(station);
    });

    return marker;
  }

  /**
   * Renderiza os marcadores no mapa com base nas estações filtradas
   */
  function renderMarkers() {
    markersLayer.clearLayers();

    filteredStations.forEach((station) => {
      const marker = createStationMarker(station);
      markersLayer.addLayer(marker);
    });

    updateCounterBadge();

    // Se houver pontos e ainda não houver seleção ativa, ajusta bounds
    if (filteredStations.length > 0 && !selectedStationKey) {
      map.fitBounds(markersLayer.getBounds().pad(0.15));
    }
  }

  /**
   * Atualiza o badge do contador de estações encontradas
   */
  function updateCounterBadge() {
    const badge = document.getElementById('stations-counter-badge');
    if (!badge) return;

    const count = filteredStations.length;
    if (count === 0) {
      badge.textContent = i18n.noLocationsFound;
    } else if (count === 1) {
      badge.textContent = `1 ${i18n.locationFound}`;
    } else {
      badge.textContent = `${count} ${i18n.locationsFound}`;
    }
  }

  /**
   * Aplica filtros de texto, DC e gratuidade
   */
  function applyFilters() {
    const query = searchQuery.trim().toLowerCase();

    filteredStations = allStations.filter((st) => {
      // 1. Busca por nome do local
      if (query && !st.local.toLowerCase().includes(query)) {
        return false;
      }
      // 2. Filtro DC
      if (filterDcOnly && !st.hasDc) {
        return false;
      }
      // 3. Filtro Apenas Gratuitos
      if (filterFreeOnly && !st.allExempt) {
        return false;
      }
      return true;
    });

    renderMarkers();

    // Se a estação selecionada não estiver mais visível nos filtros, fecha drawer
    if (selectedStationKey) {
      const exists = filteredStations.some((s) => s.key === selectedStationKey);
      if (!exists) deselectStation();
    }
  }

  /**
   * Seleciona uma estação e abre o card/drawer de detalhes
   */
  function selectStation(station) {
    selectedStationKey = station.key;

    // Atualiza classes dos marcadores no DOM
    document.querySelectorAll('.custom-station-pin').forEach((el) => {
      el.classList.remove('pin-selected');
    });

    const safeId = `pin-${station.key.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const pinEl = document.getElementById(safeId);
    if (pinEl) pinEl.classList.add('pin-selected');

    // Centraliza mapa na estação com zoom suave
    map.panTo([station.lat, station.lng], { animate: true, duration: 0.5 });

    // Preenche os dados no Drawer
    const drawer = document.getElementById('station-details-drawer');
    const nameEl = document.getElementById('drawer-station-name');
    const dcBadge = document.getElementById('drawer-dc-badge');
    const exemptBadge = document.getElementById('drawer-exempt-badge');
    const lastDateEl = document.getElementById('drawer-last-date');
    const metricCount = document.getElementById('drawer-metric-count');
    const metricKwh = document.getElementById('drawer-metric-kwh');
    const metricCusto = document.getElementById('drawer-metric-custo');
    const btnGoogle = document.getElementById('btn-nav-google-maps');
    const btnWaze = document.getElementById('btn-nav-waze');

    if (nameEl) nameEl.textContent = station.local;
    if (dcBadge) dcBadge.classList.toggle('d-none', !station.hasDc);
    if (exemptBadge) exemptBadge.classList.toggle('d-none', !station.allExempt);

    // Formata data mais recente no fuso local
    if (lastDateEl) {
      if (station.latestDate && window.DateTimeUtils) {
        lastDateEl.textContent = window.DateTimeUtils.formatDateTimeLocal(station.latestDate);
      } else if (station.latestDate) {
        lastDateEl.textContent = new Date(station.latestDate).toLocaleString();
      } else {
        lastDateEl.textContent = '-';
      }
    }

    if (metricCount) metricCount.textContent = station.count;
    if (metricKwh) {
      const kwhFmt = (station.totalKwh || 0).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 });
      metricKwh.innerHTML = `${kwhFmt} <span class="unit">kWh</span>`;
    }
    if (metricCusto) {
      if (station.allExempt) {
        metricCusto.innerHTML = `<span class="badge bg-success">${i18n.exemptLabel}</span>`;
      } else {
        const symbol = typeof window.CurrencySymbolBRL !== 'undefined' ? window.CurrencySymbolBRL : i18n.currencySymbol;
        const custoFmt = (station.totalCusto || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        metricCusto.textContent = `${symbol} ${custoFmt}`;
      }
    }

    // Links de Rotas
    if (btnGoogle) {
      btnGoogle.href = `https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lng}`;
    }
    if (btnWaze) {
      btnWaze.href = `https://waze.com/ul?ll=${station.lat},${station.lng}&navigate=yes`;
    }

    if (drawer) {
      drawer.classList.remove('d-none');
    }
  }

  /**
   * Deseleciona a estação e fecha o drawer
   */
  function deselectStation() {
    selectedStationKey = null;
    document.querySelectorAll('.custom-station-pin').forEach((el) => {
      el.classList.remove('pin-selected');
    });
    const drawer = document.getElementById('station-details-drawer');
    if (drawer) drawer.classList.add('d-none');
  }

  /**
   * Centraliza no GPS do usuário
   */
  function locateUser() {
    if (!navigator.geolocation) {
      alert(i18n.gpsError);
      return;
    }

    const gpsBtn = document.getElementById('btn-map-gps');
    if (gpsBtn) gpsBtn.classList.add('active-locating');

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (gpsBtn) gpsBtn.classList.remove('active-locating');
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        if (userLocationMarker) {
          userLocationMarker.setLatLng([lat, lng]);
        } else {
          const userIcon = L.divIcon({
            className: 'user-gps-div-icon',
            html: '<div class="user-gps-pulse"><div class="user-gps-dot"></div></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });
          userLocationMarker = L.marker([lat, lng], { icon: userIcon, title: 'Você está aqui' }).addTo(map);
        }

        map.flyTo([lat, lng], 13, { duration: 1.2 });
      },
      (err) => {
        if (gpsBtn) gpsBtn.classList.remove('active-locating');
        console.warn('Erro ao obter GPS:', err);
        alert(i18n.gpsError);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }

  /**
   * Carrega os dados de recarga via API
   */
  async function loadMapData() {
    const url = window.apiRechargesUrl || '/api/recharges/';
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(i18n.errorLoadingData);
      const recharges = await response.json();

      allStations = groupRechargesByLocation(recharges);
      filteredStations = [...allStations];

      renderMarkers();
    } catch (error) {
      console.error('Falha ao carregar dados do mapa:', error);
      const badge = document.getElementById('stations-counter-badge');
      if (badge) badge.textContent = i18n.errorLoadingData;
    }
  }

  /**
   * Configuração de Event Listeners da Interface
   */
  function setupEventListeners() {
    const searchInput = document.getElementById('map-search-input');
    const btnClearSearch = document.getElementById('btn-clear-map-search');
    const toggleDc = document.getElementById('toggle-filter-dc');
    const toggleFree = document.getElementById('toggle-filter-free');
    const btnCloseDrawer = document.getElementById('btn-close-drawer');
    const btnGps = document.getElementById('btn-map-gps');
    const btnFit = document.getElementById('btn-map-fit');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value;
        if (btnClearSearch) {
          btnClearSearch.classList.toggle('d-none', !searchQuery);
        }
        applyFilters();
      });
    }

    if (btnClearSearch) {
      btnClearSearch.addEventListener('click', () => {
        if (searchInput) {
          searchInput.value = '';
          searchQuery = '';
          btnClearSearch.classList.add('d-none');
          applyFilters();
        }
      });
    }

    if (toggleDc) {
      toggleDc.addEventListener('click', () => {
        filterDcOnly = !filterDcOnly;
        toggleDc.classList.toggle('active', filterDcOnly);
        applyFilters();
      });
    }

    if (toggleFree) {
      toggleFree.addEventListener('click', () => {
        filterFreeOnly = !filterFreeOnly;
        toggleFree.classList.toggle('active', filterFreeOnly);
        applyFilters();
      });
    }

    if (btnCloseDrawer) {
      btnCloseDrawer.addEventListener('click', deselectStation);
    }

    if (btnGps) {
      btnGps.addEventListener('click', locateUser);
    }

    if (btnFit) {
      btnFit.addEventListener('click', () => {
        if (markersLayer && markersLayer.getLayers().length > 0) {
          map.fitBounds(markersLayer.getBounds().pad(0.15));
        }
      });
    }
  }

  // Inicialização no carregamento da página
  document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('recharges-map')) {
      initMap();
      setupEventListeners();
      loadMapData();
    }
  });
})();
