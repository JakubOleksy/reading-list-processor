let items = [];
let settings = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    await loadItems();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('syncBtn').addEventListener('click', syncReadingList);
    document.getElementById('processAllBtn').addEventListener('click', () => processAll(false));
    document.getElementById('reprocessAllBtn').addEventListener('click', () => processAll(true));
    document.getElementById('settingsBtn').addEventListener('click', toggleSettings);
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('cancelSettingsBtn').addEventListener('click', toggleSettings);
}

async function loadItems() {
    try {
        const response = await fetch('/api/items');
        items = await response.json();
        renderItems();
        updateStats();
    } catch (error) {
        console.error('Error loading items:', error);
        alert('Failed to load items');
    }
}

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        settings = await response.json();
        document.getElementById('customInstructions').value = settings.custom_instructions || '';
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function syncReadingList() {
    const btn = document.getElementById('syncBtn');
    btn.disabled = true;
    btn.textContent = 'Syncing...';

    try {
        const response = await fetch('/api/sync', { method: 'POST' });
        const result = await response.json();
        alert(result.message);
        await loadItems();
    } catch (error) {
        console.error('Error syncing:', error);
        alert('Failed to sync reading list');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sync from Safari';
    }
}

async function processAll(reprocess) {
    const btn = reprocess ? document.getElementById('reprocessAllBtn') : document.getElementById('processAllBtn');
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = 'Processing...';

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reprocess })
        });
        const result = await response.json();

        if (result.errors && result.errors.length > 0) {
            console.error('Processing errors:', result.errors);
            alert(`${result.message}\n\nErrors:\n${result.errors.join('\n')}`);
        } else {
            alert(result.message);
        }

        await loadItems();
    } catch (error) {
        console.error('Error processing:', error);
        alert('Failed to process items');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

async function processItem(itemId) {
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    card.classList.add('processing');

    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, reprocess: true })
        });
        const result = await response.json();

        if (result.errors && result.errors.length > 0) {
            alert(`Processing errors:\n${result.errors.join('\n')}`);
        }

        await loadItems();
    } catch (error) {
        console.error('Error processing item:', error);
        alert('Failed to process item');
    } finally {
        card.classList.remove('processing');
    }
}

async function deleteItem(itemId) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    try {
        await fetch(`/api/items/${itemId}`, { method: 'DELETE' });
        await loadItems();
    } catch (error) {
        console.error('Error deleting item:', error);
        alert('Failed to delete item');
    }
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('hidden');
}

async function saveSettings() {
    const customInstructions = document.getElementById('customInstructions').value;

    try {
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ custom_instructions: customInstructions })
        });

        settings.custom_instructions = customInstructions;
        alert('Settings saved');
        toggleSettings();
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Failed to save settings');
    }
}

function renderItems() {
    const container = document.getElementById('itemsContainer');

    if (items.length === 0) {
        container.innerHTML = '<div class="loading">No items found. Click "Sync from Safari" to import your reading list.</div>';
        return;
    }

    container.innerHTML = items.map(item => `
        <div class="item-card" data-item-id="${item.id}">
            <div class="item-header">
                <div>
                    <div class="item-title">${escapeHtml(item.title || 'Untitled')}</div>
                    <a href="${escapeHtml(item.url)}" target="_blank" class="item-url">${escapeHtml(item.url)}</a>
                </div>
                <div class="item-actions">
                    <span class="status-badge ${item.processed ? 'status-processed' : 'status-unprocessed'}">
                        ${item.processed ? 'Processed' : 'Unprocessed'}
                    </span>
                    <button class="btn btn-primary" onclick="processItem(${item.id})">
                        ${item.processed ? 'Reprocess' : 'Process'}
                    </button>
                    <button class="btn btn-danger" onclick="deleteItem(${item.id})">Delete</button>
                </div>
            </div>

            ${item.preview_text ? `<div class="item-preview">${escapeHtml(item.preview_text)}</div>` : ''}

            ${item.summary ? `
                <div class="item-summary">
                    <h3>Summary</h3>
                    <p>${escapeHtml(item.summary)}</p>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function updateStats() {
    const total = items.length;
    const processed = items.filter(item => item.processed).length;
    const unprocessed = total - processed;

    document.getElementById('totalCount').textContent = `Total: ${total}`;
    document.getElementById('processedCount').textContent = `Processed: ${processed}`;
    document.getElementById('unprocessedCount').textContent = `Unprocessed: ${unprocessed}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
