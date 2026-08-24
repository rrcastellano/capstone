// ==================== Variáveis Globais ====================
let currentPage = 1;
let sortBy = 'data';
let sortDir = 'asc';
const pageSize = 20;

// ==================== Utilitários de Data ====================
function formatDateDisplay(value) {
    if (!value) return '';
    if (window.DateTimeUtils) {
        return window.DateTimeUtils.formatDateTimeLocal(value);
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    return d.toLocaleString();
}

function formatDateInput(value) {
    if (!value) return '';
    if (window.DateTimeUtils) {
        return window.DateTimeUtils.toLocalDatetimeInputValue(value);
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) return value;
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ==================== Função para exibir Toast ====================
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// ==================== Função para carregar recargas ====================
async function loadRecharges() {
    const params = new URLSearchParams({
        page: currentPage,
        page_size: pageSize,
        sort_by: sortBy,
        sort_dir: sortDir,
        local: document.getElementById('filter-local')?.value || '',
        observacoes: document.getElementById('filter-observacoes')?.value || '',
        isento: document.getElementById('filter-isento')?.value || '',
        date_from: document.getElementById('filter-date-from')?.value || '',
        date_to: document.getElementById('filter-date-to')?.value || ''
    });

    try {
        const response = await fetch(`/api/recharges/?${params.toString()}`);
        if (!response.ok) throw new Error(typeof ErrorLoadingRecharges !== 'undefined' ? ErrorLoadingRecharges : 'Erro ao carregar recargas');
        const data = await response.json();

        const tbody = document.getElementById('recharges-body');
        if (!tbody) return;
        tbody.innerHTML = '';

        const items = Array.isArray(data) ? data : (data.items || []);
        const total = Array.isArray(data) ? data.length : (data.total || items.length);

        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">${typeof NoRechargesFound !== 'undefined' ? NoRechargesFound : 'Nenhuma recarga encontrada.'}</td></tr>`;
        } else {
            items.forEach(item => {
                const tr = document.createElement('tr');
                tr.dataset.id = item.id;
                tr.dataset.utc = item.data;
                const custoDisplay = item.isento
                    ? `${typeof CurrencySymbolBRL !== 'undefined' ? CurrencySymbolBRL : 'R$'} 0,00 <span class="badge bg-success ms-1">ISENTO</span>`
                    : `${typeof CurrencySymbolBRL !== 'undefined' ? CurrencySymbolBRL : 'R$'} ${(item.custo || 0).toFixed(2).replace('.', ',')}`;
                const isentoBadge = item.isento
                    ? `<span class="badge bg-success">${typeof YesMessage !== 'undefined' ? YesMessage : 'Isento'}</span>`
                    : `<span class="badge bg-secondary">${typeof NoMessage !== 'undefined' ? NoMessage : 'Pago'}</span>`;
                tr.innerHTML = `
                    <td data-utc="${item.data}">${formatDateDisplay(item.data)}</td>
                    <td>${item.kwh}</td>
                    <td>${custoDisplay}</td>
                    <td>${isentoBadge}</td>
                    <td>${(item.odometro || 0).toFixed(0)}</td>
                    <td>${item.local || ''}</td>
                    <td title="${item.observacoes || ''}">${(item.observacoes || '').substring(0, 30)}${item.observacoes && item.observacoes.length > 30 ? '...' : ''}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary btn-edit">${typeof EditText !== 'undefined' ? EditText : 'Editar'}</button>
                        <button class="btn btn-sm btn-outline-danger btn-delete">${typeof DeleteText !== 'undefined' ? DeleteText : 'Excluir'}</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        const paginationInfo = document.getElementById('pagination-info');
        if (paginationInfo) {
            paginationInfo.textContent = `${typeof DisplayingText !== 'undefined' ? DisplayingText : 'Exibindo'} ${(currentPage - 1) * pageSize + 1}–${Math.min(currentPage * pageSize, total)} ${typeof OfText !== 'undefined' ? OfText : 'de'} ${total}`;
        }
        const btnPrev = document.getElementById('btn-prev-page');
        if (btnPrev) btnPrev.disabled = (data.has_prev !== undefined) ? !data.has_prev : currentPage <= 1;
        const btnNext = document.getElementById('btn-next-page');
        if (btnNext) btnNext.disabled = (data.has_next !== undefined) ? !data.has_next : (currentPage * pageSize >= total);
    } catch (error) {
        showToast(error.message, 'danger');
    }
}

// ==================== Eventos de Filtros ====================
document.getElementById('btn-apply-filters')?.addEventListener('click', () => {
    currentPage = 1;
    loadRecharges();
});

document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
    document.getElementById('filters-form')?.reset();
    currentPage = 1;
    loadRecharges();
});

document.getElementById('btn-last-30-days')?.addEventListener('click', () => {
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - 30);

    const fromInput = document.getElementById('filter-date-from');
    const toInput = document.getElementById('filter-date-to');
    if (fromInput) {
        fromInput.value = window.DateTimeUtils ? window.DateTimeUtils.toLocalDateInputValue(pastDate) : pastDate.toLocaleDateString('en-CA');
    }
    if (toInput) {
        toInput.value = window.DateTimeUtils ? window.DateTimeUtils.toLocalDateInputValue(today) : today.toLocaleDateString('en-CA');
    }
    currentPage = 1;
    loadRecharges();
});

// ==================== Paginação ====================
document.getElementById('btn-prev-page')?.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadRecharges();
    }
});

document.getElementById('btn-next-page')?.addEventListener('click', () => {
    currentPage++;
    loadRecharges();
});

// ==================== Ordenação ====================
document.querySelectorAll('#recharges-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (sortBy === field) {
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
            sortBy = field;
            sortDir = 'asc';
        }
        loadRecharges();
    });
});

// ==================== Modal de Edição ====================
function updateModalIsentoState() {
    const isentoCheck = document.getElementById('edit-isento');
    const custoField = document.getElementById('edit-custo');
    if (!isentoCheck || !custoField) return;
    if (isentoCheck.checked) {
        custoField.value = '0.00';
        custoField.readOnly = true;
        custoField.style.opacity = '0.6';
        custoField.style.cursor = 'not-allowed';
    } else {
        custoField.readOnly = false;
        custoField.style.opacity = '1';
        custoField.style.cursor = '';
    }
}

document.getElementById('edit-isento')?.addEventListener('change', updateModalIsentoState);

document.getElementById('recharges-body')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-edit')) {
        const tr = e.target.closest('tr');
        const id = tr.dataset.id;
        const utcDate = tr.dataset.utc;
        document.getElementById('edit-id').value = id;
        document.getElementById('edit-data').value = formatDateInput(utcDate || tr.children[0].textContent);
        document.getElementById('edit-kwh').value = tr.children[1].textContent;
        const isExempt = tr.children[3].textContent.includes('Isento') || tr.children[3].textContent.includes('Sim');
        document.getElementById('edit-isento').checked = isExempt;
        document.getElementById('edit-custo').value = isExempt ? '0.00' : tr.children[2].textContent.replace(/[^\d.,]/g, '').replace(',', '.');
        document.getElementById('edit-odometro').value = tr.children[4].textContent;
        document.getElementById('edit-local').value = tr.children[5].textContent;
        document.getElementById('edit-observacoes').value = tr.children[6].getAttribute('title');
        updateModalIsentoState();
        const editModal = new bootstrap.Modal(document.getElementById('editModal'));
        editModal.show();
    }
});

document.getElementById('btn-save-edit')?.addEventListener('click', async () => {
    const id = document.getElementById('edit-id').value;
    const localData = document.getElementById('edit-data').value;
    const utcIso = window.DateTimeUtils ? window.DateTimeUtils.localInputToUtcIso(localData) : (localData ? new Date(localData).toISOString() : null);
    const isExempt = document.getElementById('edit-isento').checked;

    const payload = {
        data: utcIso,
        kwh: parseFloat(document.getElementById('edit-kwh').value),
        custo: isExempt ? 0.0 : parseFloat(document.getElementById('edit-custo').value),
        odometro: parseFloat(document.getElementById('edit-odometro').value),
        isento: isExempt,
        local: document.getElementById('edit-local').value,
        observacoes: document.getElementById('edit-observacoes').value
    };

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const response = await fetch(`/api/recharges/${id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || (typeof ErrorSaveMessage !== 'undefined' ? ErrorSaveMessage : 'Erro ao salvar recarga'));
        }

        showToast(typeof RechargeUpdatedSuccess !== 'undefined' ? RechargeUpdatedSuccess : 'Recarga atualizada com sucesso', 'success');
        const editModal = bootstrap.Modal.getInstance(document.getElementById('editModal'));
        if (editModal) editModal.hide();
        loadRecharges();
    } catch (error) {
        showToast(error.message, 'danger');
    }
});

// ==================== Modal de Exclusão ====================
document.getElementById('recharges-body')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-delete')) {
        const tr = e.target.closest('tr');
        const id = tr.dataset.id;
        const confirmBtn = document.getElementById('btn-confirm-delete');
        if (confirmBtn) confirmBtn.dataset.id = id;
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
        deleteModal.show();
    }
});

document.getElementById('btn-confirm-delete')?.addEventListener('click', async () => {
    const id = document.getElementById('btn-confirm-delete').dataset.id;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const response = await fetch(`/api/recharges/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });

        if (!response.ok) throw new Error(typeof ErrorDeleteMessage !== 'undefined' ? ErrorDeleteMessage : 'Erro ao excluir recarga');

        showToast(typeof RechargeDeletedSuccess !== 'undefined' ? RechargeDeletedSuccess : 'Recarga excluída com sucesso', 'success');
        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        if (deleteModal) deleteModal.hide();
        loadRecharges();
    } catch (error) {
        showToast(error.message, 'danger');
    }
});

// ==================== Botão Exportar CSV ====================    
document.addEventListener('DOMContentLoaded', () => {
  const btnExport = document.getElementById('btn-export');
  if (!btnExport) return;

  btnExport.setAttribute('type', 'button');
  btnExport.addEventListener('click', (e) => {
    e.preventDefault();

    const getVal = (id) => document.getElementById(id)?.value || '';
    const params = new URLSearchParams({
      local:       getVal('filter-local'),
      observacoes: getVal('filter-observacoes'),
      isento:      getVal('filter-isento') || 'all',
      date_from:   getVal('filter-date-from'),
      date_to:     getVal('filter-date-to')
    });

    window.location.href = `/export_recharges?${params.toString()}`;
  });
});

// ==================== Inicialização ====================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('recharges-body')) {
        loadRecharges();
    }
});
