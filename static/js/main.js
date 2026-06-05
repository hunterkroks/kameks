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

  // Универсальный счётчик корзины в шапке. Вызывается из всех мест
  // (карточки каталога, детальная страница) с cart_total_items из ответа сервера.
  function updateCartCounter(count) {
    updateCartBadges(count);
  }

  function updateCartBadges(total) {
    // Основной badge в шапке — всегда есть в DOM (id="navbar-cart-badge")
    var main = document.getElementById('navbar-cart-badge');
    if (main) {
      main.textContent = total;
      main.style.display = total > 0 ? '' : 'none';
    }
    // Дополнительные .cart-badge если есть (виджеты на других страницах)
    document.querySelectorAll('.cart-badge:not(#navbar-cart-badge)').forEach(function(el) {
      el.textContent = total;
      el.style.display = total > 0 ? '' : 'none';
    });
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
    }).then(function(r) {
      return r.json().then(function(data) {
        if (r.status === 401 && data.redirect) {
          showToast('Войдите в аккаунт, чтобы добавить товар в корзину', 'danger');
          throw new Error('unauthenticated');
        }
        return data;
      });
    });
  }

  const cartItems = window.KAMEKS_CART || {};

  function initCartWidgets(root) {
    var scope = root || document;
    scope.querySelectorAll('.cart-widget[data-product-id]').forEach(function(widget) {
      var pid = widget.dataset.productId;
      var stock = parseInt(widget.dataset.stock || 9999, 10);
      var savedQty = parseInt(cartItems[pid] || 0, 10);
      if (savedQty > 0) setWidgetQty(widget, savedQty);

      widget.querySelector('.btn-cart-add').addEventListener('click', function() {
        cartPost('/cart/add/' + pid + '/', 'quantity=1')
          .then(function(data) {
            if (data.success) {
              stock = data.stock || stock;
              setWidgetQty(widget, data.item_quantity);
              updateCartBadges(data.cart_total);
              showToast('Товар добавлен в корзину');
              // Заблокировать + если достигли остатка
              var plusBtn = widget.querySelector('.cart-counter-plus');
              if (plusBtn) plusBtn.disabled = data.item_quantity >= stock;
            }
          })
          .catch(function(e) { if (e && e.message !== 'unauthenticated') showToast('Ошибка. Попробуйте ещё раз.', 'danger'); });
      });

      widget.querySelector('.cart-counter-plus').addEventListener('click', function() {
        var current = parseInt(widget.querySelector('.cart-counter-qty').textContent, 10);
        if (current >= stock) {
          showToast('Больше нет в наличии (' + stock + ' шт.)', 'danger');
          return;
        }
        cartPost('/cart/add/' + pid + '/', 'quantity=1')
          .then(function(data) {
            if (data.success) {
              stock = data.stock || stock;
              setWidgetQty(widget, data.item_quantity);
              updateCartBadges(data.cart_total);
              this.disabled = data.item_quantity >= stock;
            }
          }.bind(this))
          .catch(function(e) { if (e && e.message !== 'unauthenticated') showToast('Ошибка. Попробуйте ещё раз.', 'danger'); });
      });

      widget.querySelector('.cart-counter-minus').addEventListener('click', function() {
        var current = parseInt(widget.querySelector('.cart-counter-qty').textContent, 10);
        if (current <= 1) {
          cartPost('/cart/remove/' + pid + '/', '')
            .then(function(data) {
              if (data.success) {
                setWidgetQty(widget, 0);
                updateCartBadges(data.cart_total);
                var plusBtn = widget.querySelector('.cart-counter-plus');
                if (plusBtn) plusBtn.disabled = false;
              }
            })
            .catch(function(e) { if (e && e.message !== 'unauthenticated') showToast('Ошибка. Попробуйте ещё раз.', 'danger'); });
        } else {
          cartPost('/cart/add/' + pid + '/', 'quantity=' + (current - 1) + '&override=true')
            .then(function(data) {
              if (data.success) {
                stock = data.stock || stock;
                setWidgetQty(widget, data.item_quantity);
                updateCartBadges(data.cart_total);
                var plusBtn = widget.querySelector('.cart-counter-plus');
                if (plusBtn) plusBtn.disabled = data.item_quantity >= stock;
              }
            })
            .catch(function(e) { if (e && e.message !== 'unauthenticated') showToast('Ошибка. Попробуйте ещё раз.', 'danger'); });
        }
      });
    });
  }

  // Инициализируем при первой загрузке и экспортируем для AJAX-перезагрузок
  initCartWidgets(document);
  window.KAMEKS = window.KAMEKS || {};
  window.KAMEKS.initCartWidgets = function(root) { initCartWidgets(root); };
  window.KAMEKS.showToast = function(msg, type) { showToast(msg, type); };
  window.KAMEKS.updateCartBadges = function(total) { updateCartBadges(total); };
  window.KAMEKS.updateCartCounter = function(count) { updateCartCounter(count); };

  // --- Toast уведомление ---
  function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
      document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    var bg = type === 'success' ? '#1B3A5C' : '#CC2B2B';
    toast.style.cssText = 'background:' + bg + ';color:#fff;padding:12px 20px;border-radius:8px;font-size:0.9rem;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.3);opacity:0;transition:opacity 0.3s ease;max-width:280px;';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function() { toast.style.opacity = '1'; }, 10);
    setTimeout(function() {
      toast.style.opacity = '0';
      setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
  }

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

  // ─── Мега-меню (split-кнопка: стрелка открывает, ссылка — переход) ───────
  (function () {
    var trigger = document.getElementById('mega-trigger');
    var menu    = document.getElementById('mega-menu');
    var overlay = document.getElementById('mega-overlay');
    var chevron = document.getElementById('mega-chevron');
    var header  = document.querySelector('.navbar-kameks');
    if (!trigger || !menu) return;

    function getHeaderBottom() {
      if (!header) return 60;
      return header.getBoundingClientRect().bottom;
    }

    function openMenu() {
      menu.style.top = getHeaderBottom() + 'px';
      menu.classList.add('open');
      if (overlay) overlay.classList.add('show');
      trigger.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
      if (chevron) chevron.style.transform = 'rotate(180deg)';
    }

    function closeMenu() {
      menu.classList.remove('open');
      if (overlay) overlay.classList.remove('show');
      trigger.classList.remove('open');
      trigger.setAttribute('aria-expanded', 'false');
      if (chevron) chevron.style.transform = '';
    }

    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      menu.classList.contains('open') ? closeMenu() : openMenu();
    });

    if (overlay) overlay.addEventListener('click', closeMenu);

    // Пересчитываем позицию при скролле (header sticky)
    window.addEventListener('scroll', function () {
      if (menu.classList.contains('open')) {
        menu.style.top = getHeaderBottom() + 'px';
      }
    }, { passive: true });

    // Переключение правой панели по hover на раздел
    var secBtns = document.querySelectorAll('.mega-section');
    var panels  = document.querySelectorAll('.mega-right');

    secBtns.forEach(function (btn) {
      btn.addEventListener('mouseenter', function () {
        var sec = btn.dataset.sec;
        secBtns.forEach(function (b) { b.classList.remove('active'); });
        panels.forEach(function (p) { p.classList.remove('active'); });
        btn.classList.add('active');
        var panel = document.getElementById('mega-sec-' + sec);
        if (panel) panel.classList.add('active');
      });
    });

    // Закрытие по Escape / клик вне
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
    document.addEventListener('click', function (e) {
      if (!menu.contains(e.target) && !trigger.contains(e.target)) closeMenu();
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
  })();

  // ─── Каталог: раскрытие блоков фильтров ──────────────────────────────────
  window.toggleFilterBlock = function (head) {
    var block  = head.closest('.filter-block');
    var toggle = head.querySelector('.filter-toggle');
    if (!block) return;
    block.classList.toggle('collapsed');
    if (toggle) toggle.classList.toggle('rotated', block.classList.contains('collapsed'));
  };

  // ─── Каталог: дерево категорий в сайдбаре ────────────────────────────────
  window.toggleCatNode = function (el) {
    el.classList.toggle('open');
  };

  // ─── Каталог: переключение вид сетка/список ──────────────────────────────
  window.setView = function (v) {
    var grid  = document.getElementById('gridView');
    var list  = document.getElementById('listView');
    var btnG  = document.getElementById('viewGrid');
    var btnL  = document.getElementById('viewList');
    if (!grid || !list) return;
    if (v === 'grid') {
      grid.style.display = 'grid';
      list.style.display = 'none';
      if (btnG) btnG.classList.add('active');
      if (btnL) btnL.classList.remove('active');
    } else {
      grid.style.display = 'none';
      list.style.display = 'flex';
      if (btnL) btnL.classList.add('active');
      if (btnG) btnG.classList.remove('active');
    }
    try { localStorage.setItem('kameks_view', v); } catch(e) {}
  };

  // Восстанавливаем вид из localStorage
  (function () {
    var saved = '';
    try { saved = localStorage.getItem('kameks_view') || ''; } catch(e) {}
    if (saved === 'list') { window.setView('list'); }
  })();

  // ─── Каталог: мобильный сайдбар фильтров ─────────────────────────────────
  window.toggleMobileSidebar = function () {
    var sidebar = document.getElementById('catalog-sidebar');
    if (sidebar) sidebar.classList.toggle('show');
  };

  // ─── Каталог: бренд-чипсы — визуальное обновление при клике ─────────────
  document.querySelectorAll('.brand-chip').forEach(function (chip) {
    var inp = chip.querySelector('input');
    if (inp) inp.addEventListener('change', function () {
      chip.classList.toggle('sel', inp.checked);
    });
  });

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

/* ─── CHECKOUT & ORDER SUCCESS ─── */
(function () {
  'use strict';

  function phoneMask(input) {
    function format(v) {
      var d = v.replace(/\D/g, '');
      if (d.startsWith('8')) d = '7' + d.slice(1);
      if (!d.startsWith('7')) d = '7' + d;
      d = d.slice(0, 11);
      var out = '+7';
      if (d.length > 1) out += ' (' + d.slice(1, 4);
      if (d.length >= 4) out += ') ' + d.slice(4, 7);
      if (d.length >= 7) out += '-' + d.slice(7, 9);
      if (d.length >= 9) out += '-' + d.slice(9, 11);
      return out;
    }
    input.addEventListener('input', function () {
      input.value = format(input.value);
    });
    input.addEventListener('focus', function () {
      if (!input.value) input.value = '+7 ';
    });
  }
  document.querySelectorAll('.js-phone').forEach(phoneMask);
  document.querySelectorAll('.js-inn').forEach(function (el) {
    el.addEventListener('input', function () {
      el.value = el.value.replace(/\D/g, '').slice(0, 12);
    });
  });

  // --- Переключение ФЛ / ЮЛ ---
  var buyerToggle = document.getElementById('buyer-toggle');
  if (buyerToggle) {
    var btInput = document.getElementById('buyer-type-input');
    var flBlock = document.getElementById('buyer-fl');
    var ulBlock = document.getElementById('buyer-ul');
    buyerToggle.querySelectorAll('.tbt-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        buyerToggle.querySelectorAll('.tbt-btn').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        var type = btn.getAttribute('data-buyer');
        btInput.value = type;
        if (type === 'ul') {
          flBlock.style.display = 'none';
          ulBlock.style.display = '';
        } else {
          flBlock.style.display = '';
          ulBlock.style.display = 'none';
        }
      });
    });
  }

  // --- Выбор radio-карточек ---
  document.querySelectorAll('.opt-list').forEach(function (list) {
    list.querySelectorAll('.checkout-opt-card').forEach(function (card) {
      card.addEventListener('click', function () {
        list.querySelectorAll('.checkout-opt-card').forEach(function (c) { c.classList.remove('selected'); });
        card.classList.add('selected');
        var radio = card.querySelector('input[type=radio]');
        if (radio) radio.checked = true;
        // адрес для доставки
        if (list.getAttribute('data-group') === 'delivery') {
          var addr = document.getElementById('address-block');
          if (addr) {
            if (card.getAttribute('data-delivery') === 'pickup') {
              addr.style.display = 'none';
            } else {
              addr.style.display = '';
              addr.classList.add('slide-down');
            }
          }
        }
      });
    });
  });

  // --- Отправка формы: копируем ЮЛ-поля в основные, валидация ---
  var form = document.getElementById('checkout-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      var type = document.getElementById('buyer-type-input').value;
      if (type === 'ul') {
        var ulName = form.querySelector('.js-ul-name');
        var ulPhone = form.querySelector('.js-ul-phone');
        var ulEmail = form.querySelector('.js-ul-email');
        form.querySelector('[name=full_name]').value = ulName ? ulName.value : '';
        form.querySelector('input[name=phone]').value = ulPhone ? ulPhone.value : '';
        form.querySelector('input[name=email]').value = ulEmail ? ulEmail.value : '';
        var inn = (form.querySelector('[name=inn]').value || '').replace(/\D/g, '');
        if (inn.length !== 10 && inn.length !== 12) {
          e.preventDefault();
          alert('ИНН должен содержать 10 или 12 цифр');
          return;
        }
      }

      // Защита от повторной отправки: блокируем кнопку после первого клика.
      if (form.dataset.submitting === '1') {
        e.preventDefault();
        return;
      }
      form.dataset.submitting = '1';
      var btn = form.querySelector('.checkout-btn-submit');
      if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.7';
        btn.style.cursor = 'wait';
        btn.innerHTML = 'Оформляем заказ…';
      }
    });
  }

  // --- Копирование номера заказа ---
  var copyBtn = document.getElementById('copy-order');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var num = copyBtn.getAttribute('data-number');
      var done = function () {
        copyBtn.innerHTML = '<i class="bi bi-check2"></i>';
        setTimeout(function () { copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>'; }, 1800);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(num).then(done, done);
      } else {
        var t = document.createElement('textarea');
        t.value = num; document.body.appendChild(t); t.select();
        try { document.execCommand('copy'); } catch (err) {}
        document.body.removeChild(t); done();
      }
    });
  }

  // --- Раскрытие деталей заказа ---
  var dt = document.getElementById('details-toggle');
  if (dt) {
    dt.addEventListener('click', function () {
      var body = document.getElementById('details-body');
      var open = body.style.display === 'none';
      body.style.display = open ? '' : 'none';
      dt.classList.toggle('open', open);
      dt.querySelector('span').textContent = open ? 'Скрыть детали заказа' : 'Показать детали заказа';
    });
  }
})();
