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

        function openCart() {
            document.getElementById("cartDrawer").classList.remove("translate-x-full");
            document.getElementById("cartOverlay").classList.remove("hidden");
        }

        function closeCart() {
            document.getElementById("cartDrawer").classList.add("translate-x-full");
            document.getElementById("cartOverlay").classList.add("hidden");
        }


        // ✅ WISHLIST TOGGLE
        function toggleWishlist(btn, productId) {
            fetch(`/store/wishlist/toggle/${productId}/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            })
            .then(res => res.json())
            .then(data => {
                const svg = btn.querySelector('svg');
                if (data.status === 'added') {
                    svg.setAttribute('fill', '#ff7200');
                    svg.setAttribute('stroke', '#ff7200');
                    svg.classList.add('scale-110');
                    if (typeof showToast === "function") showToast("Added to wishlist ❤️");
                } else {
                    svg.setAttribute('fill', 'none');
                    svg.setAttribute('stroke', 'currentColor');
                    svg.classList.remove('scale-110');
                    if (typeof showToast === "function") showToast("Removed from wishlist");
                }
            })
            .catch(err => {
                console.error("Wishlist Error:", err);
                window.location.href = "/accounts/login/";
            });
        }

        // ✅ UPDATE CART
        function updateCart(productId, action) {
            fetch("/cart/ajax/update/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: `product_id=${productId}&action=${action}`
            })
                .then(res => res.json())
                .then(() => {
                    loadCart();
                    loadCartCount();
                });
        }

        // ✅ LOAD CART (UPGRADED UI)
        function loadCart() {
            fetch("/cart/ajax/")
                .then(res => res.json())
                .then(data => {

                    const container = document.getElementById("cartItems");
                    const total = document.getElementById("cartTotal");

                    container.innerHTML = "";

                    if (!data.items || data.items.length === 0) {
                        container.innerHTML = `
                <div class="text-center py-24 px-4">
                    <div class="text-6xl mb-6 opacity-50 grayscale mx-auto">🛍️</div>
                    <p class="text-gray-500 dark:text-gray-400 mb-6 text-lg">Your cart is empty.</p>
                    <a href="/store/" class="inline-block bg-gradient-to-r from-brandBlue to-blue-500 text-white px-8 py-3 rounded-full font-bold shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all duration-300">
                        Start Shopping
                    </a>
                </div>
            `;
                        total.innerText = "GHS 0.00";
                        return;
                    }

                    data.items.forEach(item => {
                        let variationHtml = "";
                        if(item.variations && item.variations.length > 0) {
                            variationHtml = `<p class="text-[10px] text-gray-500 mt-0.5 italic">${item.variations.join(', ')}</p>`;
                        }

                        container.innerHTML += `
                <div class="flex items-center gap-5 border-b border-gray-100 dark:border-gray-700 pb-5 pt-2 group">

                    <div class="w-20 h-20 rounded-md flex-shrink-0 bg-gray-50 dark:bg-gray-700 border border-gray-100 dark:border-gray-600 flex items-center justify-center p-2 overflow-hidden shadow-inner">
                        <img src="${item.image || ''}" class="w-full h-full object-contain drop-shadow-sm group-hover:scale-110 transition-transform duration-300">
                    </div>

                    <div class="flex-1 min-w-0 py-1">
                        <p class="text-sm font-bold text-gray-900 dark:text-white truncate mb-0.5">${item.name}</p>
                        ${variationHtml}

                        <div class="flex flex-wrap items-center gap-3 mt-2">
                            <div class="flex items-center bg-white dark:bg-gray-800 rounded-md p-0.5 border border-gray-200 dark:border-gray-600 shadow-sm">
                                <button onclick="updateCart('${item.key}', 'decrease')" class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors">−</button>
                                <span class="w-8 text-center text-sm font-bold dark:text-white">${item.quantity}</span>
                                <button onclick="updateCart('${item.key}', 'increase')" class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors">+</button>
                            </div>
                            <button onclick="updateCart('${item.key}', 'remove')" class="text-xs font-semibold text-red-500 hover:text-red-600 hover:underline transition-all">Remove</button>
                        </div>
                    </div>

                    <div class="text-right flex-shrink-0 py-1">
                        <p class="text-sm font-extrabold text-brandBlue">
                            GHS ${Number(item.total).toFixed(2)}
                        </p>
                    </div>

                </div>
            `;
                    });

                    total.innerText = "GHS " + Number(data.total).toFixed(2);
                });
        }

        // ✅ COUNT
        function loadCartCount() {
            fetch("/cart/ajax/count/")
                .then(res => res.json())
                .then(data => {
                    const badge = document.getElementById("cartCount");
                    badge.innerText = data.count;
                    badge.style.display = data.count > 0 ? "inline-block" : "none";
                });
        }

        document.addEventListener("DOMContentLoaded", function () {
            const cartOverlay = document.getElementById("cartOverlay");
            if (cartOverlay) {
                cartOverlay.addEventListener("click", closeCart);
                loadCart();
                loadCartCount();
            }
        });

        document.addEventListener("click", function (e) {
            const addBtn = e.target.closest(".card-add-to-cart-btn");
            if (addBtn) {
                const btn = addBtn;
                const productId = btn.dataset.productId;
                const productName = btn.dataset.productName || "Item";

                btn.disabled = true;
                btn.innerText = "Adding...";

                fetch("/cart/ajax/add/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    body: "product_id=" + productId
                })
                .then(res => res.json())
                .then(() => {
                    btn.disabled = false;
                    btn.innerText = "Add to Cart";
                    loadCart();
                    loadCartCount();
                    setTimeout(openCart, 150);
                    if (typeof showToast === "function") {
                        showToast(productName + " added to cart 🛒");
                    }
                });
            }
        });
