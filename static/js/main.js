/* KAMEKS — Основной JS */

document.addEventListener('DOMContentLoaded', function () {

  // --- Sticky navbar ---
  const navbar = document.querySelector('.navbar-kameks');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 50);
    });
  }

  // --- Fade-in-up анимация (старый класс) ---
  const fadeItems = document.querySelectorAll('.fade-in-up');
  if (fadeItems.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('visible'), i * 80);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    fadeItems.forEach(el => observer.observe(el));
  }

  // --- Fade-up анимация (.anim-fadeup) ---
  const fadeupItems = document.querySelectorAll('.anim-fadeup');
  if (fadeupItems.length) {
    const fadeupObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeupObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    fadeupItems.forEach(el => fadeupObs.observe(el));
  }

  // --- Анимированный счётчик цифр (data-target) ---
  function animateCounter(el) {
    const target = parseInt(el.dataset.target, 10);
    const duration = 1800;
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = Math.floor(current).toLocaleString('ru-RU') + (el.dataset.suffix || '');
    }, 16);
  }

  const counters = document.querySelectorAll('[data-target]');
  if (counters.length) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(el => counterObserver.observe(el));
  }

  // --- Анимированный счётчик для trust-bar (data-t) ---
  function animateTrustCounter(el) {
    const target = parseInt(el.dataset.t, 10);
    if (!target) return;
    const dur = target > 100 ? 2000 : 1400;
    const start = performance.now();
    (function step(now) {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * target);
      if (p < 1) requestAnimationFrame(step);
    })(start);
  }

  const trustCounters = document.querySelectorAll('[data-t]');
  if (trustCounters.length) {
    const trustObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateTrustCounter(entry.target);
          trustObs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    trustCounters.forEach(el => trustObs.observe(el));
  }

  // --- Корзина: счётчик в карточках товаров ---
  function getCsrf() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
  }

  function updateCartBadges(total) {
    document.querySelectorAll('.cart-badge').forEach(el => {
      el.textContent = total;
      el.style.display = total > 0 ? '' : 'none';
    });
    if (total > 0 && !document.querySelector('.cart-badge')) {
      document.querySelectorAll('a.navbar-icon-btn').forEach(link => {
        if (link.href && link.href.includes('/cart/')) {
          const badge = document.createElement('span');
          badge.className = 'cart-badge';
          badge.textContent = total;
          link.appendChild(badge);
        }
      });
    }
  }

  function setWidgetQty(widget, qty) {
    const addBtn  = widget.querySelector('.btn-cart-add');
    const counter = widget.querySelector('.cart-counter');
    const qtyEl   = widget.querySelector('.cart-counter-qty');
    if (qty <= 0) {
      addBtn.style.display  = '';
      counter.style.display = 'none';
    } else {
      addBtn.style.display  = 'none';
      counter.style.display = '';
      qtyEl.textContent = qty;
    }
  }

  function cartPost(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrf(),
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
    }).then(r => r.json());
  }

  const cartItems = window.KAMEKS_CART || {};
  document.querySelectorAll('.cart-widget[data-product-id]').forEach(widget => {
    const pid = widget.dataset.productId;
    const savedQty = parseInt(cartItems[pid] || 0, 10);
    if (savedQty > 0) setWidgetQty(widget, savedQty);

    widget.querySelector('.btn-cart-add').addEventListener('click', function () {
      cartPost(`/cart/add/${pid}/`, 'quantity=1')
        .then(data => {
          if (data.success) {
            setWidgetQty(widget, data.item_quantity);
            updateCartBadges(data.cart_total);
            showToast('Товар добавлен в корзину');
          }
        })
        .catch(() => showToast('Ошибка. Попробуйте ещё раз.', 'danger'));
    });

    widget.querySelector('.cart-counter-plus').addEventListener('click', function () {
      cartPost(`/cart/add/${pid}/`, 'quantity=1')
        .then(data => {
          if (data.success) {
            setWidgetQty(widget, data.item_quantity);
            updateCartBadges(data.cart_total);
          }
        })
        .catch(() => showToast('Ошибка. Попробуйте ещё раз.', 'danger'));
    });

    widget.querySelector('.cart-counter-minus').addEventListener('click', function () {
      const current = parseInt(widget.querySelector('.cart-counter-qty').textContent, 10);
      if (current <= 1) {
        cartPost(`/cart/remove/${pid}/`, '')
          .then(data => {
            if (data.success) {
              setWidgetQty(widget, 0);
              updateCartBadges(data.cart_total);
            }
          })
          .catch(() => showToast('Ошибка. Попробуйте ещё раз.', 'danger'));
      } else {
        cartPost(`/cart/add/${pid}/`, `quantity=${current - 1}&override=true`)
          .then(data => {
            if (data.success) {
              setWidgetQty(widget, data.item_quantity);
              updateCartBadges(data.cart_total);
            }
          })
          .catch(() => showToast('Ошибка. Попробуйте ещё раз.', 'danger'));
      }
    });
  });

  // --- Toast уведомление ---
  function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const bg = type === 'success' ? '#1B3A5C' : '#CC2B2B';
    toast.style.cssText = `background:${bg};color:#fff;padding:12px 20px;border-radius:8px;font-size:0.9rem;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.3);opacity:0;transition:opacity 0.3s ease;max-width:280px;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '1'; }, 10);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // --- Избранное (sessionStorage, визуальное) ---
  window.toggleFavorite = function(btn, productId) {
    const icon = btn.querySelector('i');
    const key = 'fav_' + productId;
    const isFav = sessionStorage.getItem(key);
    if (isFav) {
      sessionStorage.removeItem(key);
      icon.className = 'bi bi-heart';
      btn.style.borderColor = '';
      btn.style.color = '';
      showToast('Удалено из избранного');
    } else {
      sessionStorage.setItem(key, '1');
      icon.className = 'bi bi-heart-fill';
      btn.style.borderColor = 'var(--color-accent-red)';
      btn.style.color = 'var(--color-accent-red)';
      showToast('Добавлено в избранное');
    }
  };

  // Восстанавливаем состояние избранного при загрузке
  document.querySelectorAll('[onclick^="toggleFavorite"]').forEach(btn => {
    const match = btn.getAttribute('onclick').match(/toggleFavorite\(this,\s*(\d+)\)/);
    if (match && sessionStorage.getItem('fav_' + match[1])) {
      const icon = btn.querySelector('i');
      if (icon) icon.className = 'bi bi-heart-fill';
      btn.style.borderColor = 'var(--color-accent-red)';
      btn.style.color = 'var(--color-accent-red)';
    }
  });

  // --- Поисковая форма Hero ---
  const heroSearchForm = document.getElementById('hero-search-form');
  if (heroSearchForm) {
    heroSearchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const brand = document.getElementById('hero-brand')?.value || '';
      const model = document.getElementById('hero-model')?.value || '';
      const category = document.getElementById('hero-category')?.value || '';
      let url = '/catalog/?';
      if (brand) url += `brand=${brand}&`;
      if (category) url += `category=${category}&`;
      window.location.href = url;
    });
  }

  // --- Инициализация тикера ---
  const tickerEl = document.getElementById('ticker-track');
  if (tickerEl && !tickerEl.children.length) {
    const partners = [
      'ОАО Белкард · Гродно', 'ОАО БАТЭ · Борисов', 'ПААЗ · Полтава',
      'РААЗ · Рославль', 'ПРАМО · Москва', 'SORL · Китай',
      'Iskra · Словения', 'ОАО БРТ · Балаково', 'ЗИТ · Чернигов', 'ШААЗ · Шадринск'
    ];
    [...partners, ...partners].forEach(p => {
      const d = document.createElement('div');
      d.className = 'ticker-item';
      d.innerHTML = `<span class="ticker-dot"></span>${p}<span class="ticker-sep"></span>`;
      tickerEl.appendChild(d);
    });
  }

});
