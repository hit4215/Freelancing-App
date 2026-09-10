/* ==========================================================================
   LANCERPULSE - CORE JAVASCRIPT & REAL-TIME INTERACTION ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 0. Black & White Theme Switcher Engine (Default: White)
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeToggleIcon = document.getElementById('themeToggleIcon');
    const mobileThemeToggleBtn = document.getElementById('mobileThemeToggleBtn');
    const mobileThemeToggleIcon = document.getElementById('mobileThemeToggleIcon');
    const mobileThemeToggleText = document.getElementById('mobileThemeToggleText');

    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.add('theme-dark');
            document.documentElement.classList.add('theme-dark');
            if (themeToggleIcon) {
                themeToggleIcon.className = 'fa-solid fa-sun';
                themeToggleIcon.style.color = '#F59E0B';
            }
            if (mobileThemeToggleIcon) {
                mobileThemeToggleIcon.className = 'fa-solid fa-sun';
                mobileThemeToggleIcon.style.color = '#F59E0B';
            }
            if (mobileThemeToggleText) {
                mobileThemeToggleText.textContent = 'Switch to White Theme';
            }
            if (themeToggleBtn) {
                themeToggleBtn.setAttribute('title', 'Switch to White Theme (Default)');
            }
        } else {
            document.body.classList.remove('theme-dark');
            document.documentElement.classList.remove('theme-dark');
            if (themeToggleIcon) {
                themeToggleIcon.className = 'fa-solid fa-moon';
                themeToggleIcon.style.color = '';
            }
            if (mobileThemeToggleIcon) {
                mobileThemeToggleIcon.className = 'fa-solid fa-moon';
                mobileThemeToggleIcon.style.color = '';
            }
            if (mobileThemeToggleText) {
                mobileThemeToggleText.textContent = 'Switch to Black Theme';
            }
            if (themeToggleBtn) {
                themeToggleBtn.setAttribute('title', 'Switch to Black Theme');
            }
        }
    }

    // Initialize state from localStorage (default: 'light')
    const savedTheme = localStorage.getItem('lancerpulse_theme') || 'light';
    applyTheme(savedTheme === 'dark');

    function toggleTheme() {
        const isCurrentlyDark = document.body.classList.contains('theme-dark');
        const nextTheme = isCurrentlyDark ? 'light' : 'dark';
        localStorage.setItem('lancerpulse_theme', nextTheme);
        applyTheme(nextTheme === 'dark');
    }

    if (themeToggleBtn) themeToggleBtn.addEventListener('click', toggleTheme);
    if (mobileThemeToggleBtn) mobileThemeToggleBtn.addEventListener('click', toggleTheme);

    // 1. Mobile Drawer Navigation
    const mobileToggle = document.getElementById('mobileNavToggle');
    const mobileDrawer = document.getElementById('mobileDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');
    const drawerClose = document.getElementById('drawerClose');

    function openDrawer() {
        if (mobileDrawer) mobileDrawer.classList.add('active');
        if (drawerOverlay) drawerOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeDrawer() {
        if (mobileDrawer) mobileDrawer.classList.remove('active');
        if (drawerOverlay) drawerOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (mobileToggle) mobileToggle.addEventListener('click', openDrawer);
    if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
    if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawer);

    // 2. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-8px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // 2.5 Admin Panel Dropdown Toggle Engine
    const adminNavDropdown = document.getElementById('adminNavDropdown');
    const navAdminPanelBtn = document.getElementById('navAdminPanelBtn');
    if (adminNavDropdown && navAdminPanelBtn) {
        navAdminPanelBtn.addEventListener('click', (e) => {
            if (e.target.closest('.admin-chevron')) {
                e.preventDefault();
                adminNavDropdown.classList.toggle('open');
            }
        });

        document.addEventListener('click', (e) => {
            if (!adminNavDropdown.contains(e.target)) {
                adminNavDropdown.classList.remove('open');
            }
        });
    }

    // 3. Modal Dialog Triggers
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    const modalCloses = document.querySelectorAll('[data-modal-close]');

    modalTriggers.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    modalCloses.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // 4. Tab Switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabGroup = btn.getAttribute('data-tab-group') || 'default';
            const targetContentId = btn.getAttribute('data-tab-target');

            // Deactivate sibling buttons
            document.querySelectorAll(`.tab-btn[data-tab-group="${tabGroup}"]`).forEach(b => b.classList.remove('active'));
            // Deactivate tab contents
            document.querySelectorAll(`.tab-pane[data-tab-group="${tabGroup}"]`).forEach(pane => pane.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(targetContentId);
            if (targetPane) targetPane.classList.add('active');
        });
    });

    // 5. Chat Engine & AJAX Polling
    const chatPane = document.getElementById('chatMessagesPane');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');

    if (chatPane) {
        // Scroll to bottom immediately
        chatPane.scrollTop = chatPane.scrollHeight;

        const conversationId = chatPane.getAttribute('data-conversation-id');
        let lastMessageId = parseInt(chatPane.getAttribute('data-last-id') || '0', 10);

        // AJAX Message Submission
        if (chatForm && chatInput) {
            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const bodyText = chatInput.value.trim();
                if (!bodyText) return;

                const csrfToken = chatForm.querySelector('[name=csrfmiddlewaretoken]').value;
                const sendUrl = chatForm.getAttribute('action');

                // Clear input immediately for responsiveness
                chatInput.value = '';

                try {
                    const formData = new FormData();
                    formData.append('body', bodyText);
                    formData.append('csrfmiddlewaretoken', csrfToken);

                    const resp = await fetch(sendUrl + '?ajax=1', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });

                    if (resp.ok) {
                        const data = await resp.json();
                        if (data.status === 'success') {
                            appendMessageBubble({
                                id: data.message_id,
                                body: data.body,
                                sender: data.sender,
                                sender_avatar: data.sender_avatar,
                                created_at: data.created_at,
                                is_me: true
                            });
                            lastMessageId = Math.max(lastMessageId, data.message_id);
                        }
                    } else {
                        // Fallback submit if AJAX fails
                        chatForm.submit();
                    }
                } catch (err) {
                    console.error('Failed to send message via AJAX:', err);
                }
            });
        }

        // Periodic Polling for New Incoming Messages (every 3.5s)
        if (conversationId) {
            setInterval(async () => {
                try {
                    const fetchUrl = `/messages/${conversationId}/fetch/?last_id=${lastMessageId}`;
                    const resp = await fetch(fetchUrl);
                    if (resp.ok) {
                        const data = await resp.json();
                        if (data.status === 'success' && data.messages && data.messages.length > 0) {
                            data.messages.forEach(msg => {
                                appendMessageBubble(msg);
                                lastMessageId = Math.max(lastMessageId, msg.id);
                            });
                        }
                    }
                } catch (err) {
                    // Fail silently on polling
                }
            }, 3500);
        }

        function appendMessageBubble(msg) {
            const row = document.createElement('div');
            row.className = `message-bubble-row ${msg.is_me ? 'me' : 'other'}`;
            
            const avatarHtml = `
                <img src="${msg.sender_avatar}" alt="${msg.sender}" class="avatar-img-sm" style="width: 28px; height: 28px;">
            `;

            row.innerHTML = `
                ${avatarHtml}
                <div>
                    <div class="message-bubble">${escapeHtml(msg.body)}</div>
                    <div class="message-meta text-end" style="font-size: 0.68rem; margin-top: 2px;">
                        ${msg.created_at}
                    </div>
                </div>
            `;

            chatPane.appendChild(row);
            chatPane.scrollTo({ top: chatPane.scrollHeight, behavior: 'smooth' });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }
});
