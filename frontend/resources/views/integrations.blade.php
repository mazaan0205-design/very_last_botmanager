<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Integrations · BotManager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Material+Symbols+Outlined&display=swap" rel="stylesheet">
</head>
<body class="min-h-screen bg-slate-50 font-[Inter] text-slate-900">
    <header class="border-b border-slate-200 bg-white">
        <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <a href="{{ route('dashboard') }}" class="flex items-center gap-2 font-bold text-indigo-600"><span class="material-symbols-outlined">smart_toy</span> BotManager</a>
            <a href="{{ route('dashboard') }}" class="text-sm font-medium text-slate-600 hover:text-indigo-600">Back to agents</a>
        </div>
    </header>
    <main class="mx-auto max-w-5xl px-6 py-12">
        <p class="mb-2 text-sm font-semibold uppercase tracking-wider text-indigo-600">Connected accounts</p>
        <h1 class="text-3xl font-bold">Give agents useful tools</h1>
        <p class="mt-3 max-w-2xl text-slate-600">Connect your own Google Workspace and Slack accounts. BotManager can read Gmail, create email drafts, view calendars, prepare calendar events, and post Slack messages after your confirmation.</p>
        <div id="notice" class="mt-6 hidden rounded-lg border px-4 py-3 text-sm"></div>
        <div id="integrations" class="mt-8 grid gap-5 md:grid-cols-2"></div>
        <section class="mt-10 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
            <h2 class="font-semibold">Before connecting</h2>
            <p class="mt-1">Only the BotManager owner configures the provider app once. Each customer then signs in to their own Google or Slack account here; BotManager keeps each account connection encrypted and separate.</p>
        </section>
    </main>
    <script>
        // Dynamically inject the authenticated user's ID from Laravel securely
        const ownerId = "{{ auth()->id() ?? 'default_owner' }}";
        const backendUrl = 'http://127.0.0.1:8001';
        const container = document.getElementById('integrations');
        const notice = document.getElementById('notice');

        // Exact icon mapping
        const icons = {
            google: 'calendar_month',
            slack: 'forum',
            notion: 'edit_note'
        };

        const escapeHtml = (value) => String(value || '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));

        function showNotice(message, type = 'error') {
            notice.className = `mt-6 rounded-lg border px-4 py-3 text-sm ${type === 'error' ? 'border-red-200 bg-red-50 text-red-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`;
            notice.textContent = message;
            notice.classList.remove('hidden');
        }

        async function loadIntegrations() {
            // Master list ensuring Google, Slack, and Notion always show up together
            let items = [
                { id: 'google', name: 'Google Workspace', capabilities: ['Gmail', 'Calendar', 'Drive', 'Docs', 'Sheets'], connected: false, configured: true },
                { id: 'slack', name: 'Slack', capabilities: ['List channels', 'Post a Slack message'], connected: false, configured: false },
                { id: 'notion', name: 'Notion', capabilities: ['Search pages', 'Read pages', 'Create pages'], connected: false, configured: false }
            ];

            try {
                // Pass ownerId to fetch connection status specific to the logged-in user
                const response = await fetch(`${backendUrl}/integrations/status?owner_id=${encodeURIComponent(ownerId)}`);
                const result = await response.json();

                let backendItems = [];
                if (Array.isArray(result)) {
                    backendItems = result;
                } else if (result && typeof result === 'object') {
                    backendItems = result.integrations || result.data || result.result || Object.values(result).find(val => Array.isArray(val)) || [];
                }

                // Merge live backend statuses into our master catalog
                items = items.map(defaultItem => {
                    const found = backendItems.find(b => (b.id || '').toLowerCase() === defaultItem.id);
                    if (found) {
                        return {
                            ...defaultItem,
                            connected: !!found.connected,
                            configured: found.configured !== undefined ? found.configured : defaultItem.configured,
                            name: found.name || defaultItem.name,
                            capabilities: found.capabilities || defaultItem.capabilities
                        };
                    }
                    return defaultItem;
                });
            } catch (error) {
                console.warn("Could not fetch live statuses, using default catalog.");
            }

            container.innerHTML = items.map(item => {
                const iconKey = (item.id || 'extension').toLowerCase();
                const iconName = icons[iconKey] || 'extension';
                const badgeText = item.connected ? 'Connected' : (item.configured ? 'Ready to connect' : 'Setup required');
                const badgeClass = item.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500';
                const btnText = item.connected ? 'Account connected' : 'Connect account';
                const btnClass = item.connected ? 'cursor-not-allowed bg-slate-100 text-slate-400' : 'bg-indigo-600 text-white hover:bg-indigo-700';

                let capabilitiesText = '';
                if (Array.isArray(item.capabilities)) {
                    capabilitiesText = item.capabilities.map(escapeHtml).join(' · ');
                } else if (typeof item.capabilities === 'string') {
                    capabilitiesText = escapeHtml(item.capabilities);
                }

                return `
                    <article class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                        <div class="flex items-start justify-between">
                            <span class="material-symbols-outlined rounded-lg bg-indigo-50 p-3 text-indigo-600">${iconName}</span>
                            <span class="rounded-full px-2.5 py-1 text-xs font-semibold ${badgeClass}">${badgeText}</span>
                        </div>
                        <h2 class="mt-5 text-lg font-bold">${escapeHtml(item.name)}</h2>
                        <p class="mt-2 text-sm text-slate-600">${capabilitiesText}</p>
                        <button onclick="connectProvider('${escapeHtml(item.id)}')" ${item.connected ? 'disabled' : ''} class="mt-5 w-full rounded-lg py-2.5 text-sm font-semibold ${btnClass}">
                            ${btnText}
                        </button>
                    </article>`;
            }).join('');
        }

        async function connectProvider(provider) {
            try {
                // Include the authenticated ownerId in the connect request query string
                const response = await fetch(`${backendUrl}/integrations/${provider}/connect?owner_id=${encodeURIComponent(ownerId)}`);
                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Connection could not be started.');
                window.location.assign(data.authorization_url);
            } catch (error) {
                showNotice(error.message);
            }
        }

        loadIntegrations();
    </script>
</body>
</html>
