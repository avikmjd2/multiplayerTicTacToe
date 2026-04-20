// ── Arena Navbar ──
// Injects a unified navbar + dark mode toggle for all pages.
// Hides any existing standalone .theme-toggle fixed buttons.

(function () {
    const STYLES = `
    <style id="arena-navbar-style">
        /* Hide all existing standalone theme-toggle buttons on every page */
        .theme-toggle { display: none !important; }

        #arena-nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            height: 52px;
            background: rgba(235, 238, 242, 0.75);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(0,0,0,0.07);
            font-family: 'DM Sans', 'Inter', 'Segoe UI', sans-serif;
        }

        [data-theme="dark"] #arena-nav {
            background: rgba(19, 20, 26, 0.75);
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        /* ── Brand ── */
        #arena-nav .nav-brand {
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 5px;
            text-transform: uppercase;
            color: #3d3835;
            text-decoration: none;
            flex-shrink: 0;
            opacity: 0.85;
        }

        [data-theme="dark"] #arena-nav .nav-brand {
            color: #e2eaf4;
        }

        /* ── Center/Right group ── */
        #arena-nav .nav-actions {
            display: flex;
            align-items: center;
            order: 2; /* Keep actions on right next to brand */
        }

        /* ── Links list ── */
        #arena-nav .nav-links {
            display: flex;
            align-items: center;
            gap: 2px;
            list-style: none;
            margin: 0;
            padding: 0;
            order: 1; /* Center between brand and actions on desktop */
            flex: 1;
            justify-content: flex-end;
            margin-right: 12px;
        }

        /* ── Separator dot ── */
        #arena-nav .nav-sep {
            display: none; /* Removed dot for simpler layout */
        }

        #arena-nav .nav-links a,
        #arena-nav .nav-links button {
            display: inline-block;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 2.5px;
            text-transform: uppercase;
            text-decoration: none;
            cursor: pointer;
            transition: color 0.2s ease, opacity 0.2s ease;
            border: none;
            background: transparent;
            color: #5e5750;
            font-family: 'DM Sans', sans-serif;
            position: relative;
        }

        [data-theme="dark"] #arena-nav .nav-links a,
        [data-theme="dark"] #arena-nav .nav-links button {
            color: #94a3b8;
        }

        /* Animated underline */
        #arena-nav .nav-links a::after {
            content: '';
            position: absolute;
            bottom: 2px;
            left: 14px;
            right: 14px;
            height: 1px;
            background: #a07c38;
            transform: scaleX(0);
            transition: transform 0.2s ease;
        }

        [data-theme="dark"] #arena-nav .nav-links a::after {
            background: #fcd34d;
        }

        #arena-nav .nav-links a.active::after,
        #arena-nav .nav-links a:hover::after {
            transform: scaleX(1);
        }

        #arena-nav .nav-links a:hover { color: #a07c38; }
        #arena-nav .nav-links a.active { color: #a07c38; }

        [data-theme="dark"] #arena-nav .nav-links a:hover,
        [data-theme="dark"] #arena-nav .nav-links a.active { color: #fcd34d; }

        /* Logout */
        #arena-nav .nav-logout { color: #a0695a !important; opacity: 0.8; }
        #arena-nav .nav-logout:hover { opacity: 1 !important; }
        [data-theme="dark"] #arena-nav .nav-logout { color: #fb7185 !important; }

        /* ── Dark mode toggle inside navbar ── */
        #nav-theme-btn {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1.5px solid rgba(100,116,139,0.35);
            background: rgba(255,255,255,0.55);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-left: 10px;
            transition: background 0.2s ease, border-color 0.2s ease;
            flex-shrink: 0;
            line-height: 1;
        }

        #nav-theme-btn:hover {
            background: rgba(255,255,255,0.95);
            border-color: rgba(100,116,139,0.6);
        }

        [data-theme="dark"] #nav-theme-btn {
            border: 1.5px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.08);
        }

        [data-theme="dark"] #nav-theme-btn:hover {
            background: rgba(255,255,255,0.16);
            border-color: rgba(255,255,255,0.3);
        }

        /* Icon colors — explicit, not inherited */
        #nav-theme-btn svg { display: block; }
        #nav-theme-btn .icon-sun { display: none; }
        #nav-theme-btn .icon-moon { display: block; }
        [data-theme="dark"] #nav-theme-btn .icon-sun { display: block; }
        [data-theme="dark"] #nav-theme-btn .icon-moon { display: none; }
        /* Force visible stroke colors */
        #nav-theme-btn .icon-moon { stroke: #334155; }
        [data-theme="dark"] #nav-theme-btn .icon-sun { stroke: #fcd34d; }

        body.has-arena-nav {
            padding-top: 52px !important;
        }

        /* ── Hamburger button (hidden on desktop) ── */
        #nav-hamburger {
            display: none;
            width: 36px;
            height: 36px;
            border: none;
            background: transparent;
            cursor: pointer;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 5px;
            padding: 0;
            margin-left: 8px;
        }

        #nav-hamburger span {
            display: block;
            width: 20px;
            height: 2px;
            background: #475569;
            border-radius: 2px;
            transition: transform 0.2s ease, opacity 0.2s ease;
        }

        [data-theme="dark"] #nav-hamburger span {
            background: #94a3b8;
        }

        /* ── Mobile responsive ── */
        @media (max-width: 600px) {
            #arena-nav {
                padding: 0 16px;
                flex-wrap: nowrap; /* Don't wrap anymore */
                height: 52px;
            }

            #arena-nav .nav-brand {
                font-size: 12px;
                letter-spacing: 4px;
            }

            .nav-sep { display: none !important; }

            #nav-hamburger {
                display: flex;
            }

            #arena-nav .nav-actions {
                flex: 1;
                justify-content: flex-end;
            }

            /* Off-canvas sidebar */
            #arena-nav .nav-links {
                position: fixed;
                top: 52px;
                right: -260px;
                width: 250px;
                height: calc(100vh - 52px);
                flex-direction: column;
                background: rgba(235, 238, 242, 0.95);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-left: 1px solid rgba(0,0,0,0.07);
                border-top: 1px solid rgba(0,0,0,0.07);
                padding: 24px 0;
                margin: 0;
                transition: right 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 9998;
                align-items: stretch;
            }

            [data-theme="dark"] #arena-nav .nav-links {
                background: rgba(19, 20, 26, 0.95);
                border-left: 1px solid rgba(255,255,255,0.05);
                border-top: 1px solid rgba(255,255,255,0.05);
            }

            /* Slide in when open */
            #arena-nav .nav-links.nav-open {
                right: 0;
            }

            #arena-nav .nav-links a,
            #arena-nav .nav-links button {
                width: 100%;
                padding: 16px 24px;
                text-align: right;
                font-size: 13px;
                justify-content: flex-end;
            }

            #arena-nav .nav-links a::after {
                display: none;
            }

            /* Animated hamburger → X */
            #nav-hamburger.open span:nth-child(1) {
                transform: rotate(45deg) translate(5px, 5px);
            }
            #nav-hamburger.open span:nth-child(2) {
                opacity: 0;
            }
            #nav-hamburger.open span:nth-child(3) {
                transform: rotate(-45deg) translate(5px, -5px);
            }
        }
    </style>`;

    const THEME_BTN = `
        <button id="nav-theme-btn" title="Toggle dark mode">
            <svg class="icon-moon" width="15" height="15" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            <svg class="icon-sun" width="15" height="15" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
        </button>`;

    const HAMBURGER_BTN = `
        <button id="nav-hamburger" aria-label="Toggle menu">
            <span></span>
            <span></span>
            <span></span>
        </button>`;

    function currentPath() { return window.location.pathname; }

    function isActive(href) {
        const path = currentPath();
        if (href === '/') return path === '/' || path === '/home';
        return path.startsWith(href);
    }

    function link(href, label) {
        const active = isActive(href) ? ' class="active"' : '';
        return `<li><a href="${href}"${active}>${label}</a></li>`;
    }

    function buildAppNav() {
        return `
        <nav id="arena-nav" role="navigation" aria-label="Arena navigation">
            <a class="nav-brand" href="/">Arena</a>
            <div class="nav-actions">
                ${THEME_BTN}
                ${HAMBURGER_BTN}
            </div>
            <ul class="nav-links">
                ${link('/', 'Home')}
                ${link('/lobby', 'Lobby')}
                ${link('/leaderboard', 'Leaderboard')}
                <li>
                    <button class="nav-logout" id="nav-logout-btn">Logout</button>
                </li>
            </ul>
        </nav>`;
    }

    function buildAuthNav() {
        return `
        <nav id="arena-nav" role="navigation" aria-label="Arena navigation">
            <a class="nav-brand" href="/login">Arena</a>
            <div class="nav-actions">
                ${THEME_BTN}
                ${HAMBURGER_BTN}
            </div>
            <ul class="nav-links">
                ${link('/login', 'Login')}
                ${link('/register', 'Register')}
            </ul>
        </nav>`;
    }

    function initThemeToggle() {
        const root = document.documentElement;
        // Apply saved theme immediately (pages may already do this, but this is
        // a fallback so toggle button icon renders correctly on pages that don't)
        const saved = localStorage.getItem('lb-theme');
        if (saved === 'dark') root.setAttribute('data-theme', 'dark');

        const btn = document.getElementById('nav-theme-btn');
        if (!btn) return;

        btn.addEventListener('click', () => {
            const isDark = root.getAttribute('data-theme') === 'dark';
            if (isDark) {
                root.removeAttribute('data-theme');
                localStorage.setItem('lb-theme', 'light');
            } else {
                root.setAttribute('data-theme', 'dark');
                localStorage.setItem('lb-theme', 'dark');
            }
        });
    }

    async function init() {
        document.head.insertAdjacentHTML('beforeend', STYLES);
        document.body.classList.add('has-arena-nav');

        let isLoggedIn = false;
        try {
            const res = await fetch('/auth/whoami', { credentials: 'include' });
            if (res.ok) isLoggedIn = true;
        } catch (_) {}

        const navHTML = isLoggedIn ? buildAppNav() : buildAuthNav();
        document.body.insertAdjacentHTML('afterbegin', navHTML);

        // Logout
        const logoutBtn = document.getElementById('nav-logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                try { await fetch('/auth/logout', { method: 'POST', credentials: 'include' }); } catch (_) {}
                window.location.href = '/login';
            });
        }

        // Theme toggle
        initThemeToggle();

        // Hamburger mobile toggle
        const hamburger = document.getElementById('nav-hamburger');
        const navLinks = document.querySelector('#arena-nav .nav-links');
        if (hamburger && navLinks) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('open');
                navLinks.classList.toggle('nav-open');
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
