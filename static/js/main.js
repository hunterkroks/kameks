/* KAMEKS — Основной JS */

document.addEventListener('DOMContentLoaded', function () {

  // --- Sticky navbar ---
  const navbar = document.querySelector('.navbar-kameks');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 50);
    });
  }

  // --- Fade-in анимация при скролле ---
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

  // --- Счётчик цифр (trust bar) ---
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

  // --- AJAX: добавление в корзину ---
  document.querySelectorAll('.btn-add-to-cart[data-product-id]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const productId = this.dataset.productId;
      const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

      fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'quantity=1',
      })
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            const badge = document.querySelector('.cart-badge');
            if (badge) badge.textContent = data.cart_total;
            showToast('Товар добавлен в корзину');
          }
        })
        .catch(() => showToast('Ошибка. Попробуйте ещё раз.', 'danger'));
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
    const bg = type === 'success' ? '#2e86de' : '#c0392b';
    toast.style.cssText = `background:${bg};color:#fff;padding:12px 20px;border-radius:8px;font-size:0.9rem;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.4);opacity:0;transition:opacity 0.3s ease;max-width:280px;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '1'; }, 10);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // --- Избранное (session-based, визуальное состояние) ---
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

  // Восстанавливаем состояние избранного при загрузке страницы
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
      const brand = document.getElementById('hero-brand').value;
      const model = document.getElementById('hero-model').value;
      const category = document.getElementById('hero-category').value;
      let url = '/catalog/?';
      if (brand) url += `brand=${brand}&`;
      if (category) url += `category=${category}&`;
      window.location.href = url;
    });
  }

});
