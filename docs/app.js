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

    // 4. Cheatsheet Search & Category Filter
    initCheatsheet();

    // 5. Navbar Scroll Effect
    initNavbarScroll();

    // 6. Mobile Navigation Menu Toggle
    initMobileNav();

    // 7. Auto-resolve latest direct DMG download link from GitHub Releases
    initDirectDownload();
});

/* ========================================================
   1. Theme Toggle
   ======================================================== */
function initTheme() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Check saved preference
    const savedTheme = localStorage.getItem('bongo-theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        let newTheme = 'dark';
        if (currentTheme === 'dark' || (!currentTheme && prefersDark.matches)) {
            newTheme = 'light';
        }
        
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
   4. Cheatsheet Search & Category Filter
   ======================================================== */
function initCheatsheet() {
    const searchInput = document.getElementById('cheatsheetSearch');
    const filterBtns = document.querySelectorAll('.cat-btn');
    const tableRows = document.querySelectorAll('#cheatsheetTable tbody tr');

    let currentCategory = 'all';
    let searchQuery = '';

    function filterTable() {
        tableRows.forEach(row => {
            const cat = row.getAttribute('data-cat');
            const rowText = row.textContent.toLowerCase();

            const matchesCategory = (currentCategory === 'all' || cat === currentCategory);
            const matchesSearch = !searchQuery || rowText.includes(searchQuery);

            if (matchesCategory && matchesSearch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
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
}

/* ========================================================
   5. Navbar Scroll Effect & Scrollspy (Active Section Tracker)
   ======================================================== */
function initNavbarScroll() {
    const navbar = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    const sectionIds = ['playground', 'screenshots', 'features', 'install', 'cheatsheet', 'faq'];
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

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = navbar.classList.toggle('nav-open');
        toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close on any link click
    const links = navLinks.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', () => {
            navbar.classList.remove('nav-open');
            toggleBtn.setAttribute('aria-expanded', 'false');
        });
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!navbar.contains(e.target) && navbar.classList.contains('nav-open')) {
            navbar.classList.remove('nav-open');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && navbar.classList.contains('nav-open')) {
            navbar.classList.remove('nav-open');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    });
}

/* ========================================================
   7. Auto-Resolve Latest Direct DMG Download Link
   ======================================================== */
function initDirectDownload() {
    const downloadButtons = document.querySelectorAll('.direct-download-cta');
    if (!downloadButtons.length) return;

    const GITHUB_REPO = 'mehedishakeel/Bongo';
    const CACHE_KEY = 'bongo_latest_dmg_url';
    const CACHE_TIME_KEY = 'bongo_latest_dmg_time';
    const ONE_HOUR = 60 * 60 * 1000;

    function updateLinks(url) {
        if (!url) return;
        downloadButtons.forEach(btn => {
            btn.setAttribute('href', url);
        });
    }

    // Use cached URL if fresh to save GitHub API calls
    try {
        const cachedUrl = localStorage.getItem(CACHE_KEY);
        const cachedTime = localStorage.getItem(CACHE_TIME_KEY);
        if (cachedUrl && cachedTime && (Date.now() - parseInt(cachedTime, 10) < ONE_HOUR)) {
            updateLinks(cachedUrl);
            return;
        }
    } catch (_) {}

    // Query GitHub Releases API for the latest release asset
    fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch latest release info');
            return response.json();
        })
        .then(release => {
            if (!release || !Array.isArray(release.assets)) return;
            // Find DMG asset for macOS arm64
            const dmgAsset = release.assets.find(asset => 
                asset.name && asset.name.toLowerCase().endsWith('.dmg')
            );
            if (dmgAsset && dmgAsset.browser_download_url) {
                updateLinks(dmgAsset.browser_download_url);
                try {
                    localStorage.setItem(CACHE_KEY, dmgAsset.browser_download_url);
                    localStorage.setItem(CACHE_TIME_KEY, Date.now().toString());
                } catch (_) {}
            }
        })
        .catch(() => {
            // Keep hardcoded fallback URL already set in HTML
        });
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

