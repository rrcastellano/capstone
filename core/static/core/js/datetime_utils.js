/**
 * EVChargeLog - Utilitários de Data e Fuso Horário (UTC <-> Local)
 */
(function (global) {
  'use strict';

  const DateTimeUtils = {
    /**
     * Obtém o fuso horário atual do navegador do usuário (ex: 'America/Sao_Paulo')
     */
    getUserTimezone: function () {
      try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
      } catch (e) {
        return 'UTC';
      }
    },

    /**
     * Sincroniza o cookie 'django_timezone' para que o backend Django
     * processe requisições no mesmo fuso horário do usuário.
     */
    syncTimezoneCookie: function () {
      try {
        const tz = this.getUserTimezone();
        const cookiePrefix = 'django_timezone=';
        const cookies = document.cookie.split(';');
        let found = false;

        for (let i = 0; i < cookies.length; i++) {
          const c = cookies[i].trim();
          if (c.indexOf(cookiePrefix) === 0) {
            const currentVal = decodeURIComponent(c.substring(cookiePrefix.length));
            if (currentVal === tz) {
              found = true;
            }
            break;
          }
        }

        if (!found) {
          // Salva cookie válido por 1 ano
          document.cookie = `django_timezone=${encodeURIComponent(tz)}; path=/; max-age=31536000; SameSite=Lax`;
        }
      } catch (e) {
        console.warn('Falha ao sincronizar timezone cookie:', e);
      }
    },

    /**
     * Converte um timestamp UTC (ISO 8601 string ou objeto Date)
     * para o formato esperado por <input type="datetime-local"> no fuso local: YYYY-MM-DDTHH:mm
     */
    toLocalDatetimeInputValue: function (dateOrIso) {
      if (!dateOrIso) return '';
      const d = dateOrIso instanceof Date ? dateOrIso : new Date(dateOrIso);
      if (isNaN(d.getTime())) return '';

      const pad = (n) => String(n).padStart(2, '0');
      const year = d.getFullYear();
      const month = pad(d.getMonth() + 1);
      const day = pad(d.getDate());
      const hours = pad(d.getHours());
      const minutes = pad(d.getMinutes());

      return `${year}-${month}-${day}T${hours}:${minutes}`;
    },

    /**
     * Converte um timestamp UTC (ISO 8601 string ou objeto Date)
     * para o formato esperado por <input type="date"> no fuso local: YYYY-MM-DD
     */
    toLocalDateInputValue: function (dateOrIso) {
      if (!dateOrIso) return '';
      const d = dateOrIso instanceof Date ? dateOrIso : new Date(dateOrIso);
      if (isNaN(d.getTime())) return '';

      const pad = (n) => String(n).padStart(2, '0');
      const year = d.getFullYear();
      const month = pad(d.getMonth() + 1);
      const day = pad(d.getDate());

      return `${year}-${month}-${day}`;
    },

    /**
     * Converte o valor de um <input type="datetime-local"> (YYYY-MM-DDTHH:mm)
     * considerado no horário local do navegador para uma string ISO 8601 UTC (ex: "2026-08-19T19:13:00.000Z")
     */
    localInputToUtcIso: function (localInputStr) {
      if (!localInputStr) return '';
      // Se já for uma string ISO completa com Z ou offset, retorna normalizada
      if (localInputStr.includes('Z') || /[+-]\d{2}:\d{2}$/.test(localInputStr)) {
        const parsed = new Date(localInputStr);
        return isNaN(parsed.getTime()) ? '' : parsed.toISOString();
      }

      // Input datetime-local vem no formato "YYYY-MM-DDTHH:mm" ou "YYYY-MM-DDTHH:mm:ss"
      // new Date("YYYY-MM-DDTHH:mm") no JS interpreta como horário local
      const d = new Date(localInputStr);
      if (isNaN(d.getTime())) return '';
      return d.toISOString();
    },

    /**
     * Formata uma data UTC para exibição localizada (ex: "19/08/2026")
     */
    formatDateLocal: function (dateOrIso, locale, options) {
      if (!dateOrIso) return '';
      const d = dateOrIso instanceof Date ? dateOrIso : new Date(dateOrIso);
      if (isNaN(d.getTime())) return String(dateOrIso);

      const loc = locale || undefined;
      const opts = Object.assign({
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }, options || {});

      try {
        return new Intl.DateTimeFormat(loc, opts).format(d);
      } catch (e) {
        return d.toLocaleDateString(loc, opts);
      }
    },

    /**
     * Formata data e hora UTC para exibição localizada (ex: "19/08/2026 16:13" ou "Aug/19/2026 16:13")
     */
    formatDateTimeLocal: function (dateOrIso, locale, options) {
      if (!dateOrIso) return '';
      const d = dateOrIso instanceof Date ? dateOrIso : new Date(dateOrIso);
      if (isNaN(d.getTime())) return String(dateOrIso);

      const loc = locale || undefined;
      const opts = Object.assign({
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      }, options || {});

      try {
        return new Intl.DateTimeFormat(loc, opts).format(d);
      } catch (e) {
        return d.toLocaleString(loc, opts);
      }
    },

    /**
     * Atualiza automaticamente nós do DOM que possuam data-utc="..."
     */
    localizeDomElements: function (container) {
      const root = container || document;
      const elements = root.querySelectorAll('[data-utc]');
      elements.forEach((el) => {
        const utcStr = el.getAttribute('data-utc');
        if (!utcStr) return;
        const mode = el.getAttribute('data-date-format') || 'datetime';
        if (mode === 'date') {
          el.textContent = this.formatDateLocal(utcStr);
        } else {
          el.textContent = this.formatDateTimeLocal(utcStr);
        }
      });
    }
  };

  // Sincroniza timezone automaticamente ao carregar
  if (typeof document !== 'undefined') {
    DateTimeUtils.syncTimezoneCookie();
    document.addEventListener('DOMContentLoaded', function () {
      DateTimeUtils.localizeDomElements();
    });
  }

  // Exportação global
  global.DateTimeUtils = DateTimeUtils;
})(typeof window !== 'undefined' ? window : this);
