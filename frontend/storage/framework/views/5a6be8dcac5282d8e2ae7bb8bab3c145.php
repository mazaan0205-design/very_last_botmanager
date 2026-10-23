<!DOCTYPE html>

<html class="light" lang="en">

<head>
    <meta charset="utf-8" />
    <meta content="width=device-width, initial-scale=1.0" name="viewport" />
    <title>BotManager AI - Test Preview</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&amp;display=swap"
        rel="stylesheet" />
    <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
        rel="stylesheet" />
    <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap"
        rel="stylesheet" />
    <script id="tailwind-config">
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    "colors": {
                        "surface-container-lowest": "#ffffff",
                        "inverse-on-surface": "#f3effc",
                        "surface-variant": "#e4e1ee",
                        "primary-fixed": "#e2dfff",
                        "on-tertiary-fixed-variant": "#7b2f00",
                        "on-secondary-fixed-variant": "#38485d",
                        "on-tertiary-container": "#ffd2be",
                        "surface-tint": "#4d44e3",
                        "error": "#ba1a1a",
                        "on-surface": "#1b1b24",
                        "on-tertiary-fixed": "#351000",
                        "on-primary-fixed": "#0f0069",
                        "surface-container-low": "#f5f2ff",
                        "error-container": "#ffdad6",
                        "tertiary-fixed": "#ffdbcc",
                        "primary-fixed-dim": "#c3c0ff",
                        "surface-container-high": "#eae6f4",
                        "surface": "#fcf8ff",
                        "on-background": "#1b1b24",
                        "on-secondary-fixed": "#0b1c30",
                        "on-primary": "#ffffff",
                        "tertiary-fixed-dim": "#ffb695",
                        "surface-bright": "#fcf8ff",
                        "on-secondary-container": "#54647a",
                        "on-error-container": "#93000a",
                        "tertiary": "#7e3000",
                        "surface-container-highest": "#e4e1ee",
                        "surface-dim": "#dcd8e5",
                        "on-tertiary": "#ffffff",
                        "background": "#fcf8ff",
                        "primary": "#3525cd",
                        "outline-variant": "#c7c4d8",
                        "on-surface-variant": "#464555",
                        "inverse-surface": "#302f39",
                        "secondary-container": "#d0e1fb",
                        "on-primary-container": "#dad7ff",
                        "secondary-fixed": "#d3e4fe",
                        "on-secondary": "#ffffff",
                        "surface-container": "#f0ecf9",
                        "secondary": "#505f76",
                        "on-error": "#ffffff",
                        "inverse-primary": "#c3c0ff",
                        "primary-container": "#4f46e5",
                        "outline": "#777587",
                        "on-primary-fixed-variant": "#3323cc",
                        "secondary-fixed-dim": "#b7c8e1",
                        "tertiary-container": "#a44100"
                    },
                    "borderRadius": {
                        "DEFAULT": "0.25rem",
                        "lg": "0.5rem",
                        "xl": "0.75rem",
                        "full": "9999px"
                    },
                    "spacing": {
                        "gutter": "20px",
                        "xl": "32px",
                        "lg": "24px",
                        "xs": "4px",
                        "container-margin": "40px",
                        "md": "16px",
                        "sm": "12px",
                        "base": "8px"
                    },
                    "fontFamily": {
                        "h3": ["Inter"],
                        "body-sm": ["Inter"],
                        "body-md": ["Inter"],
                        "h1": ["Inter"],
                        "h2": ["Inter"],
                        "body-lg": ["Inter"],
                        "label-md": ["Inter"],
                        "label-sm": ["Inter"]
                    },
                    "fontSize": {
                        "h3": ["24px", {
                            "lineHeight": "32px",
                            "letterSpacing": "-0.01em",
                            "fontWeight": "600"
                        }],
                        "body-sm": ["14px", {
                            "lineHeight": "20px",
                            "fontWeight": "400"
                        }],
                        "body-md": ["16px", {
                            "lineHeight": "24px",
                            "fontWeight": "400"
                        }],
                        "h1": ["36px", {
                            "lineHeight": "44px",
                            "letterSpacing": "-0.02em",
                            "fontWeight": "700"
                        }],
                        "h2": ["30px", {
                            "lineHeight": "38px",
                            "letterSpacing": "-0.02em",
                            "fontWeight": "600"
                        }],
                        "body-lg": ["18px", {
                            "lineHeight": "28px",
                            "fontWeight": "400"
                        }],
                        "label-md": ["14px", {
                            "lineHeight": "20px",
                            "fontWeight": "500"
                        }],
                        "label-sm": ["12px", {
                            "lineHeight": "16px",
                            "letterSpacing": "0.05em",
                            "fontWeight": "600"
                        }]
                    }
                },
            },
        }
    </script>
    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }

        .message-bubble-bot {
            border-bottom-left-radius: 0.125rem;
        }

        .message-bubble-user {
            border-bottom-right-radius: 0.125rem;
        }

        ::-webkit-scrollbar {
            width: 6px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: #e2e8f0;
            border-radius: 10px;
        }
    </style>
</head>


        


        <!-- Test Interface Container -->
        <div class="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
            <!-- Quick Config Panel (Left 1/3) -->
            <section
                class="w-full lg:w-1/3 bg-slate-50 border-b lg:border-b-0 lg:border-r border-slate-200 p-4 lg:p-xl overflow-y-auto max-h-[35vh] lg:max-h-none shrink-0">
                <div class="mb-lg">
                    <h3 class="font-label-md text-on-surface-variant mb-md flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]" data-icon="tune">tune</span>
                        Model Configuration
                    </h3>
                    <div class="space-y-md">
                        <!-- Model Selection -->
                        <div class="group">
                            <label class="font-label-sm text-on-surface-variant block mb-xs">Active Engine</label>
                            <select
                                class="w-full bg-white border border-slate-200 rounded-lg px-md py-base font-body-sm focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all">
                                <option>openai/gpt-oss-120b</option>
                                <option>openai/gpt-oss-20b</option>
                            </select>
                        </div>
                        <!-- Temperature Slider -->
                        <div>
                            <div class="flex justify-between items-center mb-xs">
                                <label class="font-label-sm text-on-surface-variant">Temperature</label>
                                <span class="text-xs font-bold text-primary">0.7</span>
                            </div>
                            <input
                                class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary"
                                max="1" min="0" step="0.1" type="range" value="0.7" />
                            <div class="flex justify-between mt-xs">
                                <span class="text-[10px] text-slate-400 font-medium">Focused</span>
                                <span class="text-[10px] text-slate-400 font-medium">Creative</span>
                            </div>
                        </div>
                        <!-- System Prompt Toggle -->
                        <div
                            class="flex items-center justify-between p-md bg-white border border-slate-200 rounded-lg shadow-sm">
                            <div>
                                <h4 class="font-label-md text-on-surface">Strict Guardrails</h4>
                                <p class="text-[11px] text-slate-500">Enforce enterprise policies</p>
                            </div>
                            <button
                                class="relative inline-flex h-5 w-9 items-center rounded-full bg-primary transition-colors">
                                <span
                                    class="translate-x-4 inline-block h-4 w-4 transform rounded-full bg-white transition-transform"></span>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="mb-lg">
                    <h3 class="font-label-md text-on-surface-variant mb-md flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]"
                            data-icon="variable_insert">variable_insert</span>
                        Session Variables
                    </h3>
                    <div class="space-y-sm">
                        <div class="flex items-center gap-3">
                            <span
                                class="text-[11px] font-mono bg-slate-200 px-1.5 py-0.5 rounded text-slate-700">user_tier</span>
                            <div class="h-px flex-1 bg-slate-200"></div>
                            <span class="text-[11px] font-medium text-slate-600">Enterprise</span>
                        </div>
                        <div class="flex items-center gap-3">
                            <span
                                class="text-[11px] font-mono bg-slate-200 px-1.5 py-0.5 rounded text-slate-700">region</span>
                            <div class="h-px flex-1 bg-slate-200"></div>
                            <span class="text-[11px] font-medium text-slate-600">us-east-1</span>
                        </div>
                    </div>
                </div>
                <div class="mt-auto">
                    <button
                        class="w-full flex items-center justify-center gap-2 py-md border border-slate-200 bg-white text-slate-600 rounded-lg font-label-md hover:bg-slate-50 transition-all">
                        <span class="material-symbols-outlined text-sm" data-icon="restart_alt">restart_alt</span>
                        Reset Session
                    </button>
                </div>
            </section>
            <!-- Chat Interface (Right 2/3) -->
            <section class="flex-1 flex flex-col bg-white relative">
                <!-- Messages List -->
                <div id="messages-container"
                    class="flex-1 overflow-y-auto p-4 md:p-xl space-y-4 md:space-y-lg flex flex-col">
                    <div class="flex flex-col items-center justify-center py-xl text-center">
                        <div
                            class="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600 mb-md">
                            <span class="material-symbols-outlined text-h1" data-icon="forum">forum</span>
                        </div>
                        <h4 class="font-h3 text-on-surface mb-xs">Live Preview Session</h4>
                        <p class="text-body-sm text-slate-500 max-w-xs">Test how your bot responds to various user
                            queries in real-time. Messages are not saved to production logs.</p>
                    </div>
                    <!-- Bot Message -->
                    <div class="flex gap-2 md:gap-md max-w-[95%] md:max-w-[85%] self-start group">
                        <div
                            class="w-8 h-8 rounded-lg bg-slate-100 flex-shrink-0 flex items-center justify-center border border-slate-200">
                            <span class="material-symbols-outlined text-indigo-600 text-[18px]"
                                data-icon="robot">robot</span>
                        </div>
                        <div class="flex flex-col gap-xs">
                            <div
                                class="bg-slate-100 p-md rounded-xl text-on-surface-variant font-body-sm message-bubble-bot">
                                Hello! I'm your Customer Support AI. How can I help you with your account today?
                            </div>
                            <span class="text-[10px] text-slate-400 font-medium px-xs">Bot • 10:24 AM</span>
                        </div>
                    </div>
                    <!-- User Message -->
                    <div class="flex gap-2 md:gap-md max-w-[95%] md:max-w-[85%] self-end group">
                        <div class="flex flex-col gap-xs items-end">
                            <div
                                class="bg-primary p-md rounded-xl text-white font-body-sm message-bubble-user shadow-sm">
                                I'm having trouble accessing my billing dashboard. Can you help?
                            </div>
                            <span class="text-[10px] text-slate-400 font-medium px-xs">You • 10:25 AM</span>
                        </div>
                        <div class="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0 border border-slate-200">
                            <img alt="User" class="w-full h-full object-cover"
                                data-alt="Close up of a professional person's face for a small circular avatar"
                                src="https://lh3.googleusercontent.com/aida-public/AB6AXuA3kLj0aDFp0TVIBnKaKe8OamQtSRlErIox9jqTZRyUwMjrqP-xra4wSq9Ca588_eTB-eBK8xK-pWVgmP2ZNqJvPHBJvWytF3A3I5KSbZ0c0K5WrzKD03bZTTU17avsHZ-ucPot11NzKPFLhswUM3zzM_Y7CwnZjVAoMvYIcrpPlzLq7g14H3N-IY40RJL8aJMI_yT5TmDLGXA4NYbXsD4EHTIzxYyY_klaRLusRB54W-EyuiwtJ6Jdq8Ltsduppq8mjM6L1-a48Kg" />
                        </div>
                    </div>
                    <!-- Bot Message (Typing/Thinking State Simulation) -->
                    <div class="flex gap-2 md:gap-md max-w-[95%] md:max-w-[85%] self-start group">
                        <div
                            class="w-8 h-8 rounded-lg bg-slate-100 flex-shrink-0 flex items-center justify-center border border-slate-200">
                            <span class="material-symbols-outlined text-indigo-600 text-[18px]"
                                data-icon="robot">robot</span>
                        </div>
                        <div class="flex flex-col gap-xs">
                            <div
                                class="bg-slate-100 p-md rounded-xl text-on-surface-variant font-body-sm message-bubble-bot">
                                <div class="flex gap-1">
                                    <span class="w-1.5 h-1.5 bg-slate-400 rounded-full"></span>
                                    <span class="w-1.5 h-1.5 bg-slate-400 rounded-full opacity-60"></span>
                                    <span class="w-1.5 h-1.5 bg-slate-400 rounded-full opacity-30"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- Input Bar -->
                <div class="p-4 md:p-xl border-t border-slate-100 bg-white">
                    <div class="max-w-4xl mx-auto">
                        <div
                            class="flex items-end gap-md p-2 bg-slate-50 border border-slate-200 rounded-xl focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all shadow-sm">
                            <button class="p-2 text-slate-400 hover:text-slate-600 transition-colors">
                                <span class="material-symbols-outlined">attach_file</span>
                            </button>

                            <textarea id="chat-input"
                                class="flex-1 bg-transparent border-none focus:ring-0 text-body-sm py-2 resize-none max-h-32"
                                placeholder="Type your message..." rows="1"></textarea>

                            <button id="send-btn"
                                class="w-10 h-10 bg-primary text-white rounded-lg flex items-center justify-center hover:opacity-90 transition-all shadow-md cursor-pointer">
                                <span class="material-symbols-outlined">send</span>
                            </button>

                        </div>
                    </div>
                </div>
                <div class="flex justify-between items-center mt-sm px-xs">
                    <div class="flex gap-md">
                        <button
                            class="text-[11px] font-bold text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm" data-icon="mic">mic</span>
                            Voice Input
                        </button>
                        <button
                            class="text-[11px] font-bold text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
                            <span class="material-symbols-outlined text-sm" data-icon="history">history</span>
                            Load Prompt
                        </button>
                    </div>
                    <p class="text-[11px] text-slate-400 font-medium hidden sm:block">Press <span
                            class="font-bold">Enter</span> to send</p>
                </div>
        </div>
        </div>
        </section>
        </div>
    </main>
    <script>
        // 1. Sidebar toggle logic
        document.addEventListener('DOMContentLoaded', () => {
            const sidebar = document.getElementById('sidebar');
            const backdrop = document.getElementById('sidebar-backdrop');
            const mobileMenuBtn = document.getElementById('mobile-menu-btn');

            function toggleSidebar() {
                if (sidebar && backdrop) {
                    sidebar.classList.toggle('-translate-x-full');
                    backdrop.classList.toggle('hidden');
                }
            }

            if (mobileMenuBtn && backdrop) {
                mobileMenuBtn.addEventListener('click', toggleSidebar);
                backdrop.addEventListener('click', toggleSidebar);
            }
        });

        // 2. Unified Chat functionality
        const botId = "<?php echo e($bot->id); ?>";
        // FastAPI backend base URL, injected from Laravel (PYTHON_API_URL)
        const BASE_URL = <?php echo json_encode($apiUrl ?? 'http://127.0.0.1:8001', 15, 512) ?>;
        // Authenticated owner id (scopes Google Workspace tools to this user)
        const ownerId = "<?php echo e(auth()->id() ?? 'default_owner'); ?>";
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const messagesContainer = document.getElementById('messages-container');

        async function handleSendMessage() {
            const userText = chatInput.value.trim();
            if (!userText) return;

            // A. Add User Message to UI
            messagesContainer.innerHTML += `
            <div class="flex gap-2 md:gap-md max-w-[95%] md:max-w-[85%] self-end group">
                <div class="flex flex-col gap-xs items-end">
                    <div class="bg-primary p-md rounded-xl text-white font-body-sm shadow-sm">${userText}</div>
                    <span class="text-[10px] text-slate-400 font-medium px-xs">You • Now</span>
                </div>
            </div>`;

            chatInput.value = '';
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            // B. Fetch Request to Backend (Corrected Try block)
            try {
                const response = await fetch(`${BASE_URL}/api/bots/${botId}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: userText,
                        owner_id: ownerId,
                        history: []
                    })
                });

                if (!response.ok) {
                    let errText = '';
                    try { const errData = await response.json(); errText = errData.detail || JSON.stringify(errData); }
                    catch (e) { errText = ''; }
                    throw new Error(`HTTP ${response.status}${errText ? ': ' + errText : ''}`);
                }

                const data = await response.json();

                // C. Add Bot Reply to UI
                messagesContainer.innerHTML += `
                <div class="flex gap-2 md:gap-md max-w-[95%] md:max-w-[85%] self-start group">
                    <div class="w-8 h-8 rounded-lg bg-slate-100 flex-shrink-0 flex items-center justify-center border border-slate-200">
                        <span class="material-symbols-outlined text-indigo-600 text-[18px]">rob ot</span>
                    </div>
                    <div class="flex flex-col gap-xs">
                        <div class="bg-slate-100 p-md rounded-xl text-on-surface-variant font-body-sm">${data.reply || data.response}</div>
                    </div>
                </div>`;
                messagesContainer.scrollTop = messagesContainer.scrollHeight;

            } catch (error) {
                console.error("Fetch Error:", error);
                messagesContainer.innerHTML += `
                <div class="text-red-500 text-center text-sm p-4">Error: ${error.message || 'Could not reach the bot backend.'} (Is uvicorn running on port 8001?)</div>`;
            }
        }

        // Attach listeners
        if (sendBtn) sendBtn.addEventListener('click', handleSendMessage);
        if (chatInput) chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
    </script>
</body>

</html>
<?php /**PATH C:\Users\786\Downloads\very_last_botmanager-main (6)\very_last_botmanager-main\frontend\resources\views/test-preview.blade.php ENDPATH**/ ?>