/**
 * Cyberpunk API Editor - Frontend JavaScript
 */

// Estado da aplicação
const state = {
    currentCategory: 'characters',
    items: [],
    editingItem: null,
    affiliations: [] // Lista de afiliações carregada da API
};

// Elementos do DOM
const elements = {
    itemsContainer: document.getElementById('items-container'),
    categoryButtons: document.querySelectorAll('.category-btn'),
    modalOverlay: document.getElementById('modal-overlay'),
    editModal: document.getElementById('edit-modal'),
    closeModal: document.getElementById('close-modal'),
    cancelBtn: document.getElementById('cancel-btn'),
    editForm: document.getElementById('edit-form'),
    modalTitle: document.getElementById('modal-title'),
    imagePreview: document.getElementById('image-preview'),
    toast: document.getElementById('toast'),

    // Form fields
    itemId: document.getElementById('item-id'),
    itemCategory: document.getElementById('item-category'),
    itemName: document.getElementById('item-name'),
    itemGender: document.getElementById('item-gender'),
    itemDescription: document.getElementById('item-description'),
    itemAffiliation: document.getElementById('item-affiliation'),
    genderGroup: document.getElementById('gender-group'),
    affiliationGroup: document.getElementById('affiliation-group')
};

// ============================================
// API Functions
// ============================================

async function fetchItems(category) {
    try {
        const response = await fetch(`/api/${category}`);
        if (!response.ok) throw new Error('Erro ao carregar dados');
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showToast('Erro ao carregar dados!', true);
        return [];
    }
}

async function updateItem(category, id, data) {
    try {
        const response = await fetch(`/api/${category}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Erro ao salvar');

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Update error:', error);
        throw error;
    }
}

async function fetchAffiliations() {
    try {
        const response = await fetch('/api/affiliations');
        if (!response.ok) throw new Error('Erro ao carregar afiliações');
        return await response.json();
    } catch (error) {
        console.error('Fetch affiliations error:', error);
        return [];
    }
}

function populateAffiliationsDropdown() {
    const select = elements.itemAffiliation;
    // Limpa opções existentes exceto a primeira
    select.innerHTML = '<option value="">Selecione uma afiliação...</option>';

    // Adiciona as afiliações
    state.affiliations.forEach(aff => {
        const option = document.createElement('option');
        option.value = aff.name;
        option.textContent = aff.name;
        option.style.color = aff.color;
        select.appendChild(option);
    });
}

// ============================================
// Rendering Functions
// ============================================

function renderLoading() {
    elements.itemsContainer.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Carregando dados...</p>
        </div>
    `;
}

function renderEmpty() {
    const icons = {
        characters: '👤',
        gangs: '⚔️',
        districts: '🏙️'
    };

    elements.itemsContainer.innerHTML = `
        <div class="empty-state">
            <div class="icon">${icons[state.currentCategory]}</div>
            <p>Nenhum item encontrado nesta categoria.</p>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.5rem;">
                Execute o gerador.py para popular os dados.
            </p>
        </div>
    `;
}

function renderItems(items) {
    if (items.length === 0) {
        renderEmpty();
        return;
    }

    elements.itemsContainer.innerHTML = items.map(item => createCardHTML(item)).join('');

    // Adiciona event listeners aos cards
    document.querySelectorAll('.item-card').forEach(card => {
        card.addEventListener('click', () => openEditModal(parseInt(card.dataset.id)));
    });
}

function createCardHTML(item) {
    const imageUrl = item.images && item.images.length > 0 ? item.images[0] : null;
    const imageHTML = imageUrl
        ? `<img src="${imageUrl}" alt="${item.name}" class="card-image" onerror="this.outerHTML='<div class=\\'card-placeholder\\'>🖼️</div>'">`
        : '<div class="card-placeholder">🖼️</div>';

    const description = item.description || 'Sem descrição';

    let metaTags = '';
    if (item.gender) {
        metaTags += `<span class="meta-tag gender">${item.gender}</span>`;
    }
    if (item.affiliation && item.affiliation !== 'Unknown') {
        metaTags += `<span class="meta-tag affiliation">${item.affiliation}</span>`;
    }

    return `
        <div class="item-card" data-id="${item.id}">
            ${imageHTML}
            <div class="card-content">
                <div class="card-header">
                    <span class="card-name">${item.name}</span>
                    <span class="card-id">#${item.id}</span>
                </div>
                <p class="card-description">${description}</p>
                <div class="card-meta">${metaTags}</div>
            </div>
        </div>
    `;
}

// ============================================
// Modal Functions
// ============================================

function openEditModal(itemId) {
    const item = state.items.find(x => x.id === itemId);
    if (!item) return;

    state.editingItem = item;

    // Preenche o formulário
    elements.itemId.value = item.id;
    elements.itemCategory.value = state.currentCategory;
    elements.itemName.value = item.name || '';
    elements.itemDescription.value = item.description || '';
    elements.itemAffiliation.value = item.affiliation || '';

    // Mostra/esconde campos específicos por categoria
    if (state.currentCategory === 'characters') {
        elements.genderGroup.style.display = 'block';
        elements.affiliationGroup.style.display = 'block';
        elements.itemGender.value = item.gender || 'Male';
    } else if (state.currentCategory === 'gangs') {
        elements.genderGroup.style.display = 'none';
        elements.affiliationGroup.style.display = 'none';
    } else {
        elements.genderGroup.style.display = 'none';
        elements.affiliationGroup.style.display = 'none';
    }

    // Renderiza preview de imagens
    elements.imagePreview.innerHTML = '';
    if (item.images && item.images.length > 0) {
        elements.imagePreview.innerHTML = item.images.map(url =>
            `<img src="${url}" alt="Preview" class="preview-img" onerror="this.style.display='none'">`
        ).join('');
    }

    // Atualiza título do modal
    elements.modalTitle.textContent = `Editar: ${item.name}`;

    // Mostra o modal
    elements.modalOverlay.classList.add('active');
}

function closeEditModal() {
    elements.modalOverlay.classList.remove('active');
    state.editingItem = null;
}

// ============================================
// Form Handling
// ============================================

async function handleFormSubmit(e) {
    e.preventDefault();

    const submitBtn = elements.editForm.querySelector('button[type="submit"]');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');

    // UI de loading
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    submitBtn.disabled = true;

    try {
        const data = {
            description: elements.itemDescription.value.trim(),
        };

        // Adiciona campos específicos por categoria
        if (state.currentCategory === 'characters') {
            data.gender = elements.itemGender.value;
            data.affiliation = elements.itemAffiliation.value;
        }

        const result = await updateItem(
            state.currentCategory,
            parseInt(elements.itemId.value),
            data
        );

        showToast('✓ Salvo com sucesso!');
        closeEditModal();

        // Recarrega os dados
        await loadCategory(state.currentCategory);

    } catch (error) {
        showToast('Erro ao salvar!', true);
    } finally {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, isError = false) {
    const toast = elements.toast;
    toast.querySelector('.toast-message').textContent = message;
    toast.classList.toggle('error', isError);
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============================================
// Category Navigation
// ============================================

async function loadCategory(category) {
    state.currentCategory = category;

    // Atualiza botões ativos
    elements.categoryButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === category);
    });

    // Carrega dados
    renderLoading();
    state.items = await fetchItems(category);
    renderItems(state.items);
}

// ============================================
// Event Listeners
// ============================================

function initEventListeners() {
    // Category buttons
    elements.categoryButtons.forEach(btn => {
        btn.addEventListener('click', () => loadCategory(btn.dataset.category));
    });

    // Modal close
    elements.closeModal.addEventListener('click', closeEditModal);
    elements.cancelBtn.addEventListener('click', closeEditModal);
    elements.modalOverlay.addEventListener('click', (e) => {
        if (e.target === elements.modalOverlay) {
            closeEditModal();
        }
    });

    // Form submit
    elements.editForm.addEventListener('submit', handleFormSubmit);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeEditModal();
        }
    });
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Carrega afiliações primeiro
    state.affiliations = await fetchAffiliations();
    populateAffiliationsDropdown();

    initEventListeners();
    loadCategory('characters');
});
