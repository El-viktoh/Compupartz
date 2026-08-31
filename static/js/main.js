function getCSRFToken() {
    return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1];
}

function toggleSidebar() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const panel = document.getElementById('sidebarPanel');
    if (!sidebar || !overlay || !panel) return;

    const isVisible = !sidebar.classList.contains('invisible');

    if (isVisible) {
        overlay.classList.replace('opacity-100', 'opacity-0');
        panel.classList.replace('translate-x-0', '-translate-x-full');
        setTimeout(() => sidebar.classList.add('invisible'), 300);
        document.body.style.overflow = '';
    } else {
        sidebar.classList.remove('invisible');
        document.body.style.overflow = 'hidden';
        setTimeout(() => {
            overlay.classList.add('opacity-100');
            overlay.classList.remove('opacity-0');
            panel.classList.replace('-translate-x-full', 'translate-x-0');
        }, 10);
    }
}

function toggleWhatsapp() {
    const win = document.getElementById('whatsapp-window');
    if (win.classList.contains('opacity-0')) {
        win.classList.remove('opacity-0', 'translate-y-10', 'pointer-events-none');
        win.classList.add('opacity-100', 'translate-y-0');
    } else {
        win.classList.add('opacity-0', 'translate-y-10', 'pointer-events-none');
        win.classList.remove('opacity-100', 'translate-y-0');
    }
}

function toggleDashboardSubmenu() {
    const submenu = document.getElementById('dashboardSubmenu');
    const arrow = document.getElementById('dashboardSubArrow');
    if (submenu.classList.contains('hidden')) {
        submenu.classList.remove('hidden');
        submenu.classList.add('flex');
        arrow.classList.add('rotate-180');
    } else {
        submenu.classList.add('hidden');
        submenu.classList.remove('flex');
        arrow.classList.remove('rotate-180');
    }
}

document.addEventListener("DOMContentLoaded", function () {

    // Theme Toggle Init (multi-button support)
    const darkIcons = document.querySelectorAll('.theme-toggle-dark-icon');
    const lightIcons = document.querySelectorAll('.theme-toggle-light-icon');
    const toggleButtons = document.querySelectorAll('.theme-toggle');

    const updateIcons = () => {
        const isDark = document.documentElement.classList.contains('dark');
        darkIcons.forEach(icon => icon.classList.toggle('hidden', isDark));
        lightIcons.forEach(icon => icon.classList.toggle('hidden', !isDark));
    };

    updateIcons();

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const isDark = document.documentElement.classList.toggle('dark');
            localStorage.setItem('color-theme', isDark ? 'dark' : 'light');
            updateIcons();
        });
    });

    // Navbar Scroll Logic
    const nav = document.getElementById('main-nav');
    const handleScroll = () => {
        if (!nav) return;
        if (window.scrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    };
    window.addEventListener('scroll', handleScroll);
    handleScroll();

    // Intersection Observer for Reveal
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal-element').forEach(el => observer.observe(el));
});
