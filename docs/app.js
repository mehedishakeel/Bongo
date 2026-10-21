/**
 * Bongo · Native Apple Silicon Bengali Keyboard
 * Website Interactive Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
    // 0. Bilingual Localization (EN / BN)
    initI18n();

    // 1. Theme Toggle (Dark / Light Mode)
    initTheme();

    // 2. Interactive Playground & macOS HUD Simulation
    initPlayground();

    // 3. App Screenshots Tab Switcher
    initGallery();

    // 5. Navbar Scroll Effect
    initNavbarScroll();

    // 6. Mobile Navigation Menu Toggle
    initMobileNav();

    // 7. Interactive Multi-Architecture Download Hub
    initDownloadHub();

    // 8. Auto-resolve latest direct asset download links from GitHub Releases
    initDirectDownload();

    // 9. Installation OS Tab Switcher (macOS / Linux)
    initInstallTabs();
});

/* ========================================================
   1. Theme Toggle
   ======================================================== */
function initTheme() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Check saved preference or resolve from system
    const savedTheme = localStorage.getItem('bongo-theme');
    if (savedTheme === 'dark' || savedTheme === 'light') {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        document.documentElement.setAttribute('data-theme', prefersDark.matches ? 'dark' : 'light');
    }

    // Auto-update if user has not set an explicit override
    try {
        prefersDark.addEventListener('change', (e) => {
            if (!localStorage.getItem('bongo-theme')) {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });
    } catch (err) {}

    toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || (prefersDark.matches ? 'dark' : 'light');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('bongo-theme', newTheme);
    });
}

/* ========================================================
   2. Interactive Playground & macOS HUD Simulation
   ======================================================== */
function initPlayground() {
    const demoInput = document.getElementById('demoInput');
    const demoOutput = document.getElementById('demoOutput');
    const hudQuery = document.getElementById('hudQuery');
    const hudCandidates = document.getElementById('hudCandidates');
    const samplePills = document.querySelectorAll('.sample-pill');
    const clearBtn = document.getElementById('clearInputBtn');
    const copyBtn = document.getElementById('copyOutputBtn');

    if (!demoInput || !demoOutput) return;

    let currentCandidates = [];
    let selectedCandidateIdx = 0;

    // Helper: get current word under or right before the cursor
    function getCurrentWordContext() {
        const val = demoInput.value;
        const cursor = demoInput.selectionStart !== null ? demoInput.selectionStart : val.length;
        
        const left = val.slice(0, cursor);
        const right = val.slice(cursor);
        
        const leftMatch = left.match(/[A-Za-z0-9`~@#\$%\^&\*_\+\-=\[\]\\{}|;':",\.\/<>?]+$/);
        const rightMatch = right.match(/^[A-Za-z0-9`~@#\$%\^&\*_\+\-=\[\]\\{}|;':",\.\/<>?]+/);
        
        const start = leftMatch ? cursor - leftMatch[0].length : cursor;
        const end = rightMatch ? cursor + rightMatch[0].length : cursor;
        const word = val.slice(start, end).trim();

        return { word, start, end };
    }

    function getPlaceholderText() {
        const isBn = (document.documentElement.lang === 'bn' || window.currentLang === 'bn');
        return isBn ? 'টাইপ করার সাথে সাথে বাংলা রূপান্তর এখানে দেখা যাবে...' : 'Bangla translation will appear here as you type...';
    }

    function update() {
        const text = demoInput.value;
        
        if (clearBtn) {
            clearBtn.classList.toggle('visible', text.length > 0);
        }

        if (!text.trim()) {
            demoOutput.innerHTML = `<span class="preview-placeholder">${getPlaceholderText()}</span>`;
            hudQuery.textContent = 'ami';
            currentCandidates = window.BongoAvro ? window.BongoAvro.getCandidates('ami') : ['আমি', 'আম', 'আমায়', 'আমেরিকায়', 'আমার'];
            selectedCandidateIdx = 0;
            renderHud(currentCandidates, selectedCandidateIdx);
            return;
        }

        // Full sentence conversion using full Avro engine & smart dictionary
        if (window.BongoAvro) {
            demoOutput.textContent = window.BongoAvro.convertText(text);
        } else {
            demoOutput.textContent = text;
        }

        // Determine current word for the HUD
        const ctx = getCurrentWordContext();
        const activeWord = ctx.word || text.trim().split(/\s+/).pop();
        
        if (activeWord) {
            hudQuery.textContent = activeWord;
            if (window.BongoAvro) {
                currentCandidates = window.BongoAvro.getCandidates(activeWord);
            } else {
                currentCandidates = [activeWord];
            }
            if (selectedCandidateIdx >= currentCandidates.length) {
                selectedCandidateIdx = 0;
            }
            renderHud(currentCandidates, selectedCandidateIdx);
        }
    }

    function renderHud(candidates, selectedIdx) {
        if (!hudCandidates) return;
        hudCandidates.innerHTML = '';
        candidates.forEach((cand, idx) => {
            const row = document.createElement('div');
            row.className = `hud-row ${idx === selectedIdx ? 'selected' : ''}`;
            row.innerHTML = `
                <span class="hud-badge">${idx + 1}</span>
                <span class="hud-text">${cand}</span>
            `;
            row.addEventListener('click', () => {
                selectCandidate(idx);
            });
            hudCandidates.appendChild(row);
        });
    }

    function selectCandidate(idx) {
        if (!currentCandidates || !currentCandidates[idx]) return;
        const choice = currentCandidates[idx];
        const ctx = getCurrentWordContext();
        const val = demoInput.value;
        
        if (ctx.word && ctx.start !== undefined && ctx.end !== undefined) {
            const before = val.slice(0, ctx.start);
            const after = val.slice(ctx.end);
            demoInput.value = before + choice + (after.startsWith(' ') ? after : ' ' + after);
            const newPos = (before + choice + ' ').length;
            demoInput.setSelectionRange(newPos, newPos);
        } else {
            demoInput.value = (val.trim() + ' ' + choice).trim() + ' ';
        }
        
        selectedCandidateIdx = 0;
        update();
        demoInput.focus();
    }

    // Keyboard navigation in HUD: ArrowUp, ArrowDown, Tab, Enter
    demoInput.addEventListener('keydown', (e) => {
        if (!currentCandidates || currentCandidates.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedCandidateIdx = (selectedCandidateIdx + 1) % currentCandidates.length;
            renderHud(currentCandidates, selectedCandidateIdx);
            return;
        }

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedCandidateIdx = (selectedCandidateIdx - 1 + currentCandidates.length) % currentCandidates.length;
            renderHud(currentCandidates, selectedCandidateIdx);
            return;
        }

        if (e.key === 'Tab' || e.key === 'Enter') {
            if (currentCandidates.length > 0) {
                e.preventDefault();
                selectCandidate(selectedCandidateIdx);
                return;
            }
        }
    });

    demoInput.addEventListener('input', () => {
        selectedCandidateIdx = 0;
        update();
    });

    demoInput.addEventListener('click', update);
    demoInput.addEventListener('keyup', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            update();
        }
    });

    // Language change sync for placeholder
    window.addEventListener('bongo-lang-change', () => {
        if (!demoInput.value.trim()) {
            demoOutput.innerHTML = `<span class="preview-placeholder">${getPlaceholderText()}</span>`;
        }
    });

    // Sample pills
    samplePills.forEach(pill => {
        pill.addEventListener('click', () => {
            const sample = pill.getAttribute('data-text');
            demoInput.value = sample;
            selectedCandidateIdx = 0;
            update();
            demoInput.focus();
        });
    });

    // Clear button
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            demoInput.value = '';
            selectedCandidateIdx = 0;
            update();
            demoInput.focus();
        });
    }

    // Copy Output button
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const textToCopy = demoOutput.textContent.trim();
            const placeholderText = getPlaceholderText();
            if (!textToCopy || textToCopy === placeholderText || textToCopy.includes('রূপান্তর')) return;

            function showCopied() {
                const btnText = copyBtn.querySelector('.copy-btn-text');
                const origText = btnText ? btnText.textContent : 'Copy';
                copyBtn.classList.add('copied');
                const isBn = (document.documentElement.lang === 'bn' || window.currentLang === 'bn');
                if (btnText) btnText.textContent = isBn ? 'কপি হয়েছে! ✓' : 'Copied! ✓';
                setTimeout(() => {
                    copyBtn.classList.remove('copied');
                    if (btnText) btnText.textContent = origText;
                }, 2000);
            }

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(textToCopy).then(showCopied).catch(() => {
                    fallbackCopy(textToCopy, showCopied);
                });
            } else {
                fallbackCopy(textToCopy, showCopied);
            }
        });
    }

    function fallbackCopy(text, cb) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand('copy');
            cb();
        } catch (err) {
            // ignore
        }
        document.body.removeChild(ta);
    }

    // Initial render
    update();
}

/* ========================================================
   3. App Screenshots Tab Switcher
   ======================================================== */
function initGallery() {
    const tabBtns = document.querySelectorAll('.gallery-tab-btn');
    const tabItems = document.querySelectorAll('.gallery-item');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');

            tabBtns.forEach(b => b.classList.remove('active'));
            tabItems.forEach(item => item.classList.remove('active'));

            btn.classList.add('active');
            const targetItem = document.getElementById(targetId);
            if (targetItem) {
                targetItem.classList.add('active');
            }
        });
    });
}

/* ========================================================
   4. Cheatsheet Search, Category Filter & Compact Toggle
   ======================================================== */
function initCheatsheet() {
    const searchInput = document.getElementById('cheatsheetSearch');
    if (!searchInput) return;
    const filterBtns = document.querySelectorAll('.cat-btn');
    const tableRows = document.querySelectorAll('#cheatsheetTable tbody tr');
    const countEl = document.getElementById('cheatsheetCount');
    const scrollContainer = document.querySelector('.table-scroll-container');
    const toggleBtn = document.getElementById('toggleCheatsheetHeight');

    let currentCategory = 'all';
    let searchQuery = '';
    const totalCount = tableRows.length;

    function updateCount(visibleCount) {
        if (!countEl) return;
        const lang = document.documentElement.lang || 'en';
        const t = (window.BONGO_TRANSLATIONS && window.BONGO_TRANSLATIONS[lang]) || {};
        if (visibleCount === totalCount && !searchQuery && currentCategory === 'all') {
            countEl.textContent = t['cheatsheet.count_all'] || `Showing all ${totalCount} characters`;
        } else {
            const template = t['cheatsheet.count_filtered'] || `Showing ${visibleCount} matching characters`;
            countEl.textContent = template.replace('{count}', visibleCount);
        }
    }

    function filterTable() {
        let visibleCount = 0;
        tableRows.forEach(row => {
            const cat = row.getAttribute('data-cat');
            const rowText = row.textContent.toLowerCase();

            const matchesCategory = (currentCategory === 'all' || cat === currentCategory);
            const matchesSearch = !searchQuery || rowText.includes(searchQuery);

            if (matchesCategory && matchesSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        updateCount(visibleCount);
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            filterTable();
        });
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.getAttribute('data-category');
            filterTable();
        });
    });

    if (toggleBtn && scrollContainer) {
        toggleBtn.addEventListener('click', () => {
            const isExpanded = scrollContainer.classList.toggle('is-expanded');
            toggleBtn.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
            const expandIcon = toggleBtn.querySelector('.toggle-icon-expand');
            const collapseIcon = toggleBtn.querySelector('.toggle-icon-collapse');
            const toggleText = toggleBtn.querySelector('.toggle-text');
            if (expandIcon) expandIcon.style.display = isExpanded ? 'none' : 'inline-block';
            if (collapseIcon) collapseIcon.style.display = isExpanded ? 'inline-block' : 'none';
            const lang = document.documentElement.lang || 'en';
            const t = (window.BONGO_TRANSLATIONS && window.BONGO_TRANSLATIONS[lang]) || {};
            if (toggleText) {
                toggleText.textContent = isExpanded
                    ? (t['cheatsheet.collapse'] || 'Collapse to Compact View')
                    : (t['cheatsheet.expand'] || 'View Full Table');
            }
        });
    }

    window.addEventListener('bongo-lang-change', () => {
        let visibleCount = 0;
        tableRows.forEach(row => {
            if (row.style.display !== 'none') visibleCount++;
        });
        updateCount(visibleCount);

        if (toggleBtn && scrollContainer) {
            const isExpanded = scrollContainer.classList.contains('is-expanded');
            const lang = document.documentElement.lang || 'en';
            const t = (window.BONGO_TRANSLATIONS && window.BONGO_TRANSLATIONS[lang]) || {};
            const toggleText = toggleBtn.querySelector('.toggle-text');
            if (toggleText) {
                toggleText.textContent = isExpanded
                    ? (t['cheatsheet.collapse'] || 'Collapse to Compact View')
                    : (t['cheatsheet.expand'] || 'View Full Table');
            }
        }
    });

    // Initial count
    updateCount(totalCount);
}

/* ========================================================
   5. Navbar Scroll Effect & Scrollspy (Active Section Tracker)
   ======================================================== */
function initNavbarScroll() {
    const navbar = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    const sectionIds = ['playground', 'screenshots', 'features', 'install', 'faq'];
    const sections = sectionIds
        .map(id => document.getElementById(id))
        .filter(sec => sec !== null);

    // 1. Navbar elevation shadow on scroll
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            navbar.style.boxShadow = 'var(--shadow-md)';
        } else {
            navbar.style.boxShadow = 'none';
        }
    }, { passive: true });

    // 2. Smooth scrolling click handler for navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetId = link.getAttribute('href').slice(1);
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                e.preventDefault();
                targetEl.scrollIntoView({ behavior: 'smooth' });
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
                if (history.pushState) {
                    history.pushState(null, null, '#' + targetId);
                }
            }
        });
    });

    // 3. Scrollspy: automatically detect active section in viewport
    function updateActiveNav() {
        const scrollPosition = window.scrollY + 140; // 140px offset for sticky navbar + top padding
        let currentSectionId = '';

        for (let i = sections.length - 1; i >= 0; i--) {
            const sec = sections[i];
            if (sec.offsetTop <= scrollPosition) {
                currentSectionId = sec.id;
                break;
            }
        }

        // If at the very top of hero, clear active section
        if (window.scrollY < 200) {
            currentSectionId = '';
        }

        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === '#' + currentSectionId) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav, { passive: true });
    window.addEventListener('resize', updateActiveNav, { passive: true });
    updateActiveNav();
}

/* ========================================================
   6. Mobile Navigation Menu Toggle
   ======================================================== */
function initMobileNav() {
    const navbar = document.getElementById('navbar');
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const navLinks = document.getElementById('navLinks');
    if (!navbar || !toggleBtn || !navLinks) return;

    function closeMenu() {
        navbar.classList.remove('nav-open');
        navLinks.classList.remove('mobile-open');
        toggleBtn.setAttribute('aria-expanded', 'false');
    }

    function toggleMenu(e) {
        if (e) e.stopPropagation();
        const isOpen = navbar.classList.toggle('nav-open');
        navLinks.classList.toggle('mobile-open', isOpen);
        toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }

    toggleBtn.addEventListener('click', toggleMenu);

    // Close on any link click
    const links = navLinks.querySelectorAll('a, button');
    links.forEach(link => {
        link.addEventListener('click', () => {
            closeMenu();
        });
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!navbar.contains(e.target) && (navbar.classList.contains('nav-open') || navLinks.classList.contains('mobile-open'))) {
            closeMenu();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && (navbar.classList.contains('nav-open') || navLinks.classList.contains('mobile-open'))) {
            closeMenu();
        }
    });
}

/* ========================================================
   7. Interactive Multi-Architecture Download Hub
   ======================================================== */
function initDownloadHub() {
    const hubTabs = document.querySelectorAll('.dl-tab-btn');
    const macPanel = document.getElementById('dl-panel-mac');
    const linuxPanel = document.getElementById('dl-panel-linux');
    const winPanel = document.getElementById('dl-panel-windows');
    const androidPanel = document.getElementById('dl-panel-android');
    const copyBtn = document.getElementById('copyInstallCmd');
    const copyText = document.getElementById('copyCmdText');

    if (!hubTabs.length || !macPanel || !linuxPanel) return;

    function switchHub(os, syncInstall = true) {
        hubTabs.forEach(tab => {
            const tabOs = tab.getAttribute('data-hub-os');
            const isActive = tabOs === os;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        if (macPanel) macPanel.style.display = (os === 'mac') ? 'flex' : 'none';
        if (linuxPanel) linuxPanel.style.display = (os === 'linux') ? 'flex' : 'none';
        if (winPanel) winPanel.style.display = (os === 'windows') ? 'flex' : 'none';
        if (androidPanel) androidPanel.style.display = (os === 'android') ? 'flex' : 'none';

        if (syncInstall && typeof window.switchInstallTab === 'function') {
            window.switchInstallTab(os, false);
        }
    }

    window.switchDownloadHub = switchHub;
    window.switchHub = switchHub;

    hubTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            const btn = e.currentTarget || tab;
            const os = btn.getAttribute('data-hub-os');
            if (os) {
                switchHub(os);
            }
        });
    });

    // Auto-detect OS
    try {
        const ua = navigator.userAgent || '';
        if (/Android/i.test(ua)) {
            switchHub('android');
        } else if (/Win/i.test(ua)) {
            switchHub('windows');
        } else if (/Linux|X11/i.test(ua)) {
            switchHub('linux');
        } else {
            switchHub('mac');
        }
    } catch (_) {}

    // Copy Linux terminal command button
    if (copyBtn && copyText) {
        copyBtn.addEventListener('click', async () => {
            const cmd = 'curl -sSL https://raw.githubusercontent.com/mehedishakeel/Bongo/main/platforms/linux/scripts/install.sh | bash';
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(cmd);
                } else {
                    const ta = document.createElement('textarea');
                    ta.value = cmd;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                }
                const prev = copyText.textContent;
                copyText.textContent = 'Copied! ✓';
                setTimeout(() => {
                    copyText.textContent = prev;
                }, 2000);
            } catch (_) {}
        });
    }

    // Copy macOS Homebrew command button
    const copyMacBtn = document.getElementById('copyMacBrewCmd');
    const copyMacText = document.getElementById('copyMacCmdText');
    if (copyMacBtn && copyMacText) {
        copyMacBtn.addEventListener('click', async () => {
            const cmd = 'brew install --cask mehedishakeel/bongo/bongo';
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(cmd);
                } else {
                    const ta = document.createElement('textarea');
                    ta.value = cmd;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                }
                const prev = copyMacText.textContent;
                copyMacText.textContent = 'Copied! ✓';
                setTimeout(() => {
                    copyMacText.textContent = prev;
                }, 2000);
            } catch (_) {}
        });
    }

    // Copy Windows PowerShell command button
    const copyWinBtn = document.getElementById('copyWinCmd');
    const copyWinText = document.getElementById('copyWinCmdText');
    if (copyWinBtn && copyWinText) {
        copyWinBtn.addEventListener('click', async () => {
            const cmd = 'powershell -c "irm https://raw.githubusercontent.com/mehedishakeel/Bongo/main/platforms/windows/scripts/install.ps1 | iex"';
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(cmd);
                } else {
                    const ta = document.createElement('textarea');
                    ta.value = cmd;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                }
                const prev = copyWinText.textContent;
                copyWinText.textContent = 'Copied! ✓';
                setTimeout(() => {
                    copyWinText.textContent = prev;
                }, 2000);
            } catch (_) {}
        });
    }
}

/* ========================================================
   8. Auto-Resolve Latest Direct Multi-Arch Download Links
   ======================================================== */
function initDirectDownload() {
    const GITHUB_REPO = 'mehedishakeel/Bongo';
    const CACHE_KEY = 'bongo_latest_assets_v1_1_0';
    const CACHE_TIME_KEY = 'bongo_latest_assets_time_v1_1_0';
    const ONE_HOUR = 60 * 60 * 1000;

    function applyAssetUrls(assets) {
        if (!assets || !Array.isArray(assets)) return;

        assets.forEach(asset => {
            const name = (asset.name || '').toLowerCase();
            const url = asset.browser_download_url;
            if (!url) return;

            if (name.endsWith('.dmg')) {
                if (name.includes('universal')) {
                    document.querySelectorAll('.download-mac-universal').forEach(el => el.setAttribute('href', url));
                } else if (name.includes('arm64')) {
                    document.querySelectorAll('.download-mac-arm64').forEach(el => el.setAttribute('href', url));
                } else if (name.includes('intel') || name.includes('x86_64')) {
                    document.querySelectorAll('.download-mac-x86').forEach(el => el.setAttribute('href', url));
                }
            } else if (name.endsWith('.deb')) {
                if (name.includes('amd64') || name.includes('x86_64')) {
                    document.querySelectorAll('.download-linux-amd64').forEach(el => el.setAttribute('href', url));
                } else if (name.includes('arm64') || name.includes('aarch64')) {
                    document.querySelectorAll('.download-linux-arm64').forEach(el => el.setAttribute('href', url));
                }
            } else if (name.endsWith('.exe')) {
                document.querySelectorAll('.download-windows-exe').forEach(el => el.setAttribute('href', url));
            } else if (name.endsWith('.msi')) {
                document.querySelectorAll('.download-windows-msi').forEach(el => el.setAttribute('href', url));
            } else if (name.endsWith('.zip')) {
                document.querySelectorAll('.download-windows-zip').forEach(el => el.setAttribute('href', url));
            } else if (name.endsWith('.apk')) {
                document.querySelectorAll('.download-android-apk').forEach(el => el.setAttribute('href', url));
            }
        });
    }

    try {
        const cached = localStorage.getItem(CACHE_KEY);
        const cachedTime = localStorage.getItem(CACHE_TIME_KEY);
        if (cached && cachedTime && (Date.now() - parseInt(cachedTime, 10) < ONE_HOUR)) {
            applyAssetUrls(JSON.parse(cached));
            return;
        }
    } catch (_) {}

    fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`)
        .then(res => res.ok ? res.json() : null)
        .then(release => {
            if (release && Array.isArray(release.assets)) {
                applyAssetUrls(release.assets);
                try {
                    localStorage.setItem(CACHE_KEY, JSON.stringify(release.assets));
                    localStorage.setItem(CACHE_TIME_KEY, Date.now().toString());
                } catch (_) {}
            }
        })
        .catch(() => {});
}

/* ========================================================
   8. Bilingual Localization (EN / BN)
   ======================================================== */
function initI18n() {
    const translations = window.BONGO_TRANSLATIONS;
    if (!translations) return;

    const desktopToggle = document.getElementById('langToggle');
    const desktopLangText = document.getElementById('langText');
    const mobileToggle = document.getElementById('mobileLangToggle');
    const mobileLangText = document.getElementById('mobileLangText');

    const STORAGE_KEY = 'bongo_lang';

    function getInitialLang() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'en' || saved === 'bn') return saved;
        } catch (_) {}

        const browserLang = (navigator.languages && navigator.languages[0]) || navigator.language || '';
        if (browserLang.toLowerCase().startsWith('bn')) {
            return 'bn';
        }
        return 'en';
    }

    let currentLang = getInitialLang();

    function setLanguage(lang) {
        if (!translations[lang]) return;
        currentLang = lang;
        document.documentElement.setAttribute('lang', lang);

        try {
            localStorage.setItem(STORAGE_KEY, lang);
        } catch (_) {}

        const dict = translations[lang];

        // 1. Update document title
        if (dict['page.title']) {
            document.title = dict['page.title'];
        }

        // 2. Update all elements with data-i18n
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (key && dict[key] !== undefined) {
                let text = dict[key];
                if (typeof text === 'string') {
                    text = text.replace(/&copy;/g, '©');
                }
                if (/<[a-z][\s\S]*>/i.test(text) || /&[a-z0-9#]+;/i.test(text)) {
                    el.innerHTML = text;
                } else {
                    el.textContent = text;
                }
            }
        });

        // 3. Update inputs with data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (key && dict[key] !== undefined) {
                el.setAttribute('placeholder', dict[key]);
            }
        });

        // 4. Update elements with data-i18n-title
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            if (key && dict[key] !== undefined) {
                el.setAttribute('title', dict[key]);
            }
        });

        // 5. Update elements with data-i18n-aria
        document.querySelectorAll('[data-i18n-aria]').forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            if (key && dict[key] !== undefined) {
                el.setAttribute('aria-label', dict[key]);
            }
        });

        // 6. Update toggles labels and accessible titles
        if (desktopLangText) {
            desktopLangText.textContent = lang === 'en' ? 'বাংলা' : 'EN';
        }
        if (desktopToggle) {
            const btnTitle = lang === 'en' ? 'বাংলা সংস্করণে পড়ুন' : 'Read in English';
            desktopToggle.setAttribute('title', btnTitle);
            desktopToggle.setAttribute('aria-label', btnTitle);
        }

        if (mobileLangText) {
            mobileLangText.textContent = lang === 'en' ? 'বাংলা সংস্করণ (Bangla)' : 'English Version';
        }
        if (mobileToggle) {
            const mobileAria = lang === 'en' ? 'বাংলা সংস্করণে পরিবর্তন করুন' : 'Switch to English version';
            mobileToggle.setAttribute('aria-label', mobileAria);
        }

        window.dispatchEvent(new CustomEvent('bongo-lang-change', { detail: { lang } }));
    }

    function toggleLanguage() {
        const nextLang = currentLang === 'en' ? 'bn' : 'en';
        setLanguage(nextLang);
    }

    if (desktopToggle) {
        desktopToggle.addEventListener('click', toggleLanguage);
    }
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleLanguage);
    }

    // Apply language on load
    setLanguage(currentLang);
}

/* ========================================================
   8. Installation OS Tab Switcher
   ======================================================== */
function initInstallTabs() {
    const tabs = document.querySelectorAll('.os-tab-btn');
    const macSteps = document.getElementById('steps-mac');
    const linuxSteps = document.getElementById('steps-linux');
    const winSteps = document.getElementById('steps-windows');
    const androidSteps = document.getElementById('steps-android');
    if (!tabs.length || !macSteps || !linuxSteps) return;

    function switchInstallTab(os, syncHub = true) {
        tabs.forEach(t => {
            const tabOs = t.getAttribute('data-os');
            const isActive = tabOs === os;
            t.classList.toggle('active', isActive);
            t.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        if (macSteps) macSteps.style.display = (os === 'mac') ? 'grid' : 'none';
        if (linuxSteps) linuxSteps.style.display = (os === 'linux') ? 'grid' : 'none';
        if (winSteps) winSteps.style.display = (os === 'windows') ? 'grid' : 'none';
        if (androidSteps) androidSteps.style.display = (os === 'android') ? 'grid' : 'none';

        if (syncHub && typeof window.switchDownloadHub === 'function') {
            window.switchDownloadHub(os, false);
        }
    }

    window.switchInstallTab = switchInstallTab;

    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            const btn = e.currentTarget || tab;
            const os = btn.getAttribute('data-os');
            if (os) {
                switchInstallTab(os);
            }
        });
    });
}

/* ========================================================
   10. Built-in Utilities: Unicode ↔ Bijoy (ANSI) Converter
   ======================================================== */
function initConverter() {
    const modeU2BBtn = document.getElementById('convModeU2B');
    const modeB2UBtn = document.getElementById('convModeB2U');
    const swapBtn = document.getElementById('btnSwapDirection');

    const inputArea = document.getElementById('convInputText');
    const outputArea = document.getElementById('convOutputText');

    const inputLabel = document.getElementById('convInputLabel');
    const inputBadge = document.getElementById('convInputBadge');
    const outputLabel = document.getElementById('convOutputLabel');
    const outputBadge = document.getElementById('convOutputBadge');

    const inputCharCount = document.getElementById('convInputCharCount');
    const inputWordCount = document.getElementById('convInputWordCount');
    const outputCharCount = document.getElementById('convOutputCharCount');
    const outputWordCount = document.getElementById('convOutputWordCount');

    const clearBtn = document.getElementById('btnClearConvInput');
    const copyBtn = document.getElementById('btnCopyConvOutput');
    const copyBtnText = document.getElementById('convCopyBtnText');

    const samplePills = document.querySelectorAll('.conv-sample-pill');

    if (!inputArea || !outputArea) return;

    let currentMode = 'u2b'; // 'u2b' or 'b2u'

    function countWords(str) {
        const trimmed = (str || '').trim();
        if (!trimmed) return 0;
        return trimmed.split(/\s+/).length;
    }

    function updateStats() {
        const inVal = inputArea.value || '';
        const outVal = outputArea.value || '';

        const inChars = inVal.length;
        const inWords = countWords(inVal);
        const outChars = outVal.length;
        const outWords = countWords(outVal);

        if (inputCharCount) inputCharCount.textContent = `${inChars} chars`;
        if (inputWordCount) inputWordCount.textContent = `${inWords} words`;
        if (outputCharCount) outputCharCount.textContent = `${outChars} chars`;
        if (outputWordCount) outputWordCount.textContent = `${outWords} words`;
    }

    function performConversion() {
        const text = inputArea.value || '';
        if (!window.BongoConverter) {
            outputArea.value = text;
            updateStats();
            return;
        }

        if (!text) {
            outputArea.value = '';
            updateStats();
            return;
        }

        if (currentMode === 'u2b') {
            outputArea.value = window.BongoConverter.unicodeToBijoy(text);
        } else {
            outputArea.value = window.BongoConverter.bijoyToUnicode(text);
        }

        updateStats();
    }

    function setMode(mode) {
        currentMode = mode;
        const isU2B = mode === 'u2b';

        if (modeU2BBtn) {
            modeU2BBtn.classList.toggle('active', isU2B);
            modeU2BBtn.setAttribute('aria-selected', isU2B ? 'true' : 'false');
        }
        if (modeB2UBtn) {
            modeB2UBtn.classList.toggle('active', !isU2B);
            modeB2UBtn.setAttribute('aria-selected', !isU2B ? 'true' : 'false');
        }

        if (inputBadge) inputBadge.textContent = isU2B ? 'Unicode' : 'Bijoy (ANSI)';
        if (outputBadge) outputBadge.textContent = isU2B ? 'Bijoy (ANSI)' : 'Unicode';

        if (isU2B) {
            inputArea.classList.remove('bijoy-font');
            outputArea.classList.add('bijoy-font');
            inputArea.placeholder = "Type or paste Unicode Bangla text here (e.g. আমি বাংলায় গান গাই)...";
        } else {
            inputArea.classList.add('bijoy-font');
            outputArea.classList.remove('bijoy-font');
            inputArea.placeholder = "Type or paste Bijoy ANSI text here (e.g. Avwg evsjvq Mvb MvB)...";
        }

        performConversion();
    }

    function swapDirection() {
        const currentOutput = outputArea.value || '';
        const targetMode = currentMode === 'u2b' ? 'b2u' : 'u2b';
        inputArea.value = currentOutput;
        setMode(targetMode);
        inputArea.focus();
    }

    // Attach Event Listeners
    if (modeU2BBtn) {
        modeU2BBtn.addEventListener('click', () => setMode('u2b'));
    }
    if (modeB2UBtn) {
        modeB2UBtn.addEventListener('click', () => setMode('b2u'));
    }
    if (swapBtn) {
        swapBtn.addEventListener('click', swapDirection);
    }

    inputArea.addEventListener('input', performConversion);
    inputArea.addEventListener('paste', () => {
        setTimeout(performConversion, 20);
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            inputArea.value = '';
            outputArea.value = '';
            updateStats();
            inputArea.focus();
        });
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const textToCopy = outputArea.value || '';
            if (!textToCopy) return;

            navigator.clipboard.writeText(textToCopy).then(() => {
                const origText = copyBtnText ? copyBtnText.textContent : 'Copy Output';
                if (copyBtnText) copyBtnText.textContent = 'Copied!';
                copyBtn.classList.add('copied');
                setTimeout(() => {
                    if (copyBtnText) copyBtnText.textContent = origText;
                    copyBtn.classList.remove('copied');
                }, 2000);
            }).catch(() => {
                outputArea.select();
                document.execCommand('copy');
            });
        });
    }

    samplePills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            const sampleText = e.currentTarget.getAttribute('data-sample');
            if (sampleText) {
                setMode('u2b');
                inputArea.value = sampleText;
                performConversion();
                inputArea.focus();
            }
        });
    });

    // Initial pass
    updateStats();
}
