/* ════════════════════════════════════════════════════════════
   Логика страницы корзины КАМЭКС.
   Использует существующие endpoints add/remove + новые
   (promo, delivery, save-later, restore, email, invoice).
   ════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var URLS = window.CART_URLS || {};
  var FREE = window.CART_FREE_THRESHOLD || 50000;

  function csrf() {
    return (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  }
  function fmt(n) {
    return Math.round(n).toLocaleString('ru-RU') + ' ₽';
  }
  function post(url, params) {
    var body = new URLSearchParams();
    Object.keys(params || {}).forEach(function (k) { body.set(k, params[k]); });
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrf(),
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); });
  }

  // ── Общий счётчик в шапке (main.js) ──
  function updateHeaderCounter(total) {
    if (window.KAMEKS && window.KAMEKS.updateCartCounter) window.KAMEKS.updateCartCounter(total);
    else {
      var b = document.getElementById('navbar-cart-badge');
      if (b) { b.textContent = total; b.style.display = total > 0 ? '' : 'none'; }
    }
  }
  function updateHeadBadge(unique, count) {
    var el = document.getElementById('cart-head-badge');
    if (!el) return;
    var word = unique === 1 ? 'товар' : 'товара';
    el.textContent = unique + ' ' + word + ' · ' + count + ' шт.';
  }

  // ── Тост (через main.js если есть) ──
  function toast(msg, type) {
    if (window.KAMEKS && window.KAMEKS.showToast) { window.KAMEKS.showToast(msg, type); return; }
    alert(msg);
  }

  // ════════ СОСТОЯНИЕ ИТОГА ════════
  var state = {
    itemsTotal: 0,
    discountPct: 0,
    deliveryMethod: 'pickup',
    deliveryBase: { pickup: 0, cdek: 450, dellin: 680 },
  };

  function deliveryCost() {
    if (state.deliveryMethod === 'pickup') return 0;
    if (state.itemsTotal >= FREE) return 0;
    return state.deliveryBase[state.deliveryMethod] || 0;
  }

  function recalcSidebar() {
    var discount = state.itemsTotal * state.discountPct / 100;
    var delivery = deliveryCost();
    var total = state.itemsTotal - discount + delivery;

    var itemsEl = document.getElementById('cart-total-items');
    if (itemsEl) itemsEl.textContent = fmt(state.itemsTotal);

    var discRow = document.getElementById('cart-total-discount-row');
    var discEl = document.getElementById('cart-total-discount');
    var saveEl = document.getElementById('cart-total-save');
    var saveVal = document.getElementById('cart-total-save-val');
    if (discount > 0) {
      if (discRow) discRow.style.display = '';
      if (discEl) discEl.textContent = '−' + fmt(discount);
      if (saveEl) saveEl.style.display = '';
      if (saveVal) saveVal.textContent = Math.round(discount).toLocaleString('ru-RU');
    } else {
      if (discRow) discRow.style.display = 'none';
      if (saveEl) saveEl.style.display = 'none';
    }

    var delEl = document.getElementById('cart-total-delivery');
    if (delEl) delEl.textContent = delivery > 0 ? fmt(delivery) : 'бесплатно';

    var finalEl = document.getElementById('cart-total-final');
    if (finalEl) finalEl.textContent = fmt(total);

    // Цены в радиокнопках доставки
    document.querySelectorAll('.cart-delivery-cost[data-base]').forEach(function (el) {
      var base = parseInt(el.dataset.base, 10);
      el.textContent = state.itemsTotal >= FREE ? 'бесплатно' : (base + ' ₽');
    });

    updateFreeship();
  }

  function updateFreeship() {
    var block = document.getElementById('cart-freeship');
    if (!block) return;
    var remaining = Math.max(0, FREE - state.itemsTotal);
    var progress = Math.min(100, state.itemsTotal / FREE * 100);
    var fill = document.getElementById('cart-freeship-fill');
    var remEl = document.getElementById('cart-freeship-remaining');
    if (state.itemsTotal >= FREE) {
      block.innerHTML = '<div class="cart-freeship-done"><i class="bi bi-check-circle-fill me-2"></i>У вас бесплатная доставка по России!</div>';
    } else {
      if (fill) fill.style.width = progress + '%';
      if (remEl) remEl.textContent = fmt(remaining);
    }
  }

  // Инициализация state из DOM
  (function initState() {
    var itemsEl = document.getElementById('cart-total-items');
    if (itemsEl) state.itemsTotal = parseFloat(itemsEl.textContent.replace(/[^\d]/g, '')) || 0;
    var pctEl = document.getElementById('cart-promo-pct');
    var applied = document.getElementById('cart-promo-applied');
    if (pctEl && applied && applied.style.display !== 'none') {
      state.discountPct = parseInt(pctEl.textContent, 10) || 0;
    }
    var checked = document.querySelector('input[name="delivery"]:checked');
    if (checked) state.deliveryMethod = checked.value;
  })();

  // ════════ КОЛИЧЕСТВО ════════
  function syncQty(pid, qty, stock) {
    document.querySelectorAll('.qty-btn[data-product-id="' + pid + '"]').forEach(function (btn) {
      btn.dataset.current = qty;
      if (btn.dataset.action === 'plus') {
        var dis = stock > 0 && qty >= stock;
        btn.disabled = dis; btn.style.opacity = dis ? '0.4' : '1';
      }
      if (btn.dataset.action === 'minus') {
        btn.disabled = qty <= 1; btn.style.opacity = qty <= 1 ? '0.4' : '1';
      }
    });
  }

  document.querySelectorAll('.qty-btn').forEach(function (btn) {
    syncQty(btn.dataset.productId, parseInt(btn.dataset.current, 10), parseInt(btn.dataset.stock, 10));
    btn.addEventListener('click', function () {
      var pid = this.dataset.productId;
      var action = this.dataset.action;
      var url = this.dataset.addUrl;
      var stock = parseInt(this.dataset.stock, 10);
      var qty = parseInt(document.getElementById('qty-' + pid).textContent, 10);
      if (action === 'plus') qty = stock > 0 ? Math.min(qty + 1, stock) : qty + 1;
      else qty = Math.max(qty - 1, 1);

      document.getElementById('qty-' + pid).textContent = qty;
      syncQty(pid, qty, stock);

      post(url, { quantity: qty, override: 'true' }).then(function (res) {
        var d = res.data;
        if (d.success) {
          var tot = document.getElementById('total-' + pid);
          if (tot) tot.textContent = fmt(d.item_total);
          var realQty = d.item_quantity !== undefined ? d.item_quantity : d.cart_quantity;
          document.getElementById('qty-' + pid).textContent = realQty;
          syncQty(pid, realQty, d.stock || stock);
          state.itemsTotal = d.cart_grand_total;
          updateHeaderCounter(d.cart_total !== undefined ? d.cart_total : d.cart_total_items);
          updateHeadBadge(document.querySelectorAll('.cart-row').length, d.cart_total !== undefined ? d.cart_total : d.cart_total_items);
          recalcSidebar();
        }
      }).catch(function () { toast('Ошибка обновления', 'danger'); });
    });
  });

  // ════════ УДАЛЕНИЕ ════════
  function animateRemoveRow(pid, after) {
    var row = document.getElementById('cart-row-' + pid);
    if (!row) { if (after) after(); return; }
    row.style.transition = 'opacity .25s, transform .25s';
    row.style.opacity = '0';
    row.style.transform = 'translateX(20px)';
    setTimeout(function () { row.remove(); if (after) after(); }, 260);
  }

  function checkEmpty() {
    if (document.querySelectorAll('.cart-row').length === 0) window.location.reload();
  }

  document.querySelectorAll('.remove-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var pid = this.dataset.productId;
      var url = this.dataset.removeUrl;
      post(url, {}).then(function (res) {
        var d = res.data;
        animateRemoveRow(pid, function () {
          if (d.success) {
            state.itemsTotal = d.cart_grand_total;
            updateHeaderCounter(d.cart_total);
            updateHeadBadge(document.querySelectorAll('.cart-row').length, d.cart_total);
            recalcSidebar();
          }
          checkEmpty();
        });
      }).catch(function () { toast('Ошибка удаления', 'danger'); });
    });
  });

  // ════════ ОЧИСТИТЬ КОРЗИНУ ════════
  var clearBtn = document.getElementById('cart-clear-btn');
  if (clearBtn) clearBtn.addEventListener('click', function () {
    if (!confirm('Очистить корзину? Все товары будут удалены.')) return;
    var removes = Array.prototype.map.call(document.querySelectorAll('.remove-btn'), function (b) {
      return post(b.dataset.removeUrl, {});
    });
    Promise.all(removes).then(function () { window.location.reload(); });
  });

  // ════════ ОТЛОЖИТЬ / ВЕРНУТЬ ════════
  document.querySelectorAll('.cart-row-savelater').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var pid = this.dataset.productId;
      var url = this.dataset.url;
      post(url, {}).then(function (res) {
        var d = res.data;
        if (d.success) {
          animateRemoveRow(pid, function () {
            state.itemsTotal = d.cart_grand_total;
            updateHeaderCounter(d.cart_total);
            updateHeadBadge(document.querySelectorAll('.cart-row').length, d.cart_total);
            recalcSidebar();
            toast('Товар отложен. Обновите страницу, чтобы увидеть его в «Отложенных».', 'success');
            checkEmpty();
          });
        }
      }).catch(function () { toast('Ошибка', 'danger'); });
    });
  });

  document.querySelectorAll('.cart-saved-restore').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var sid = this.dataset.savedId;
      var url = this.dataset.url;
      post(url, {}).then(function (res) {
        var d = res.data;
        if (d.success) {
          var card = document.getElementById('saved-' + sid);
          if (card) card.remove();
          updateHeaderCounter(d.cart_total);
          toast('Возвращено в корзину', 'success');
          setTimeout(function () { window.location.reload(); }, 600);
        }
      }).catch(function () { toast('Ошибка', 'danger'); });
    });
  });

  // ════════ РЕКОМЕНДАЦИИ: В КОРЗИНУ ════════
  document.querySelectorAll('.reco-add-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var url = this.dataset.url;
      var self = this;
      post(url, { quantity: 1 }).then(function (res) {
        var d = res.data;
        if (res.ok && d.success) {
          updateHeaderCounter(d.cart_total !== undefined ? d.cart_total : d.cart_total_items);
          self.innerHTML = '<i class="bi bi-check-lg me-1"></i>Добавлено';
          toast('Товар добавлен в корзину', 'success');
          setTimeout(function () { window.location.reload(); }, 800);
        } else {
          toast((d && d.message) || 'Не удалось добавить', 'danger');
        }
      }).catch(function () { toast('Ошибка', 'danger'); });
    });
  });

  // ════════ ПРОМОКОД ════════
  var promoApply = document.getElementById('cart-promo-apply');
  if (promoApply) promoApply.addEventListener('click', function () {
    var input = document.getElementById('cart-promo-input');
    var err = document.getElementById('cart-promo-error');
    var code = (input.value || '').trim();
    if (!code) { err.textContent = 'Введите код'; err.style.display = ''; return; }
    err.style.display = 'none';
    post(URLS.applyPromo, { code: code }).then(function (res) {
      var d = res.data;
      if (res.ok && d.success) {
        state.discountPct = d.discount_percent;
        document.getElementById('cart-promo-form').style.display = 'none';
        document.getElementById('cart-promo-applied').style.display = '';
        document.getElementById('cart-promo-pct').textContent = d.discount_percent;
        recalcSidebar();
      } else {
        err.textContent = (d && d.error) || 'Промокод не принят';
        err.style.display = '';
      }
    }).catch(function () { err.textContent = 'Ошибка соединения'; err.style.display = ''; });
  });

  var promoRemove = document.getElementById('cart-promo-remove');
  if (promoRemove) promoRemove.addEventListener('click', function () {
    post(URLS.removePromo, {}).then(function () {
      state.discountPct = 0;
      document.getElementById('cart-promo-applied').style.display = 'none';
      document.getElementById('cart-promo-form').style.display = '';
      var input = document.getElementById('cart-promo-input');
      if (input) input.value = '';
      recalcSidebar();
    });
  });

  // ════════ ДОСТАВКА ════════
  document.querySelectorAll('.cart-delivery-opt').forEach(function (opt) {
    opt.addEventListener('click', function () {
      var method = this.dataset.method;
      var radio = this.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
      document.querySelectorAll('.cart-delivery-opt').forEach(function (o) { o.classList.remove('sel'); });
      this.classList.add('sel');
      state.deliveryMethod = method;
      recalcSidebar();
      post(URLS.setDelivery, { method: method }).then(function (res) {
        var d = res.data;
        if (d.success) { state.itemsTotal = d.items_total; recalcSidebar(); }
      });
    });
  });

  // ════════ МОДАЛКИ ════════
  function openModal(id) {
    var m = document.getElementById(id);
    if (m) { m.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
  }
  function closeModal(m) {
    m.style.display = 'none'; document.body.style.overflow = '';
  }
  document.querySelectorAll('.cart-modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay || e.target.hasAttribute('data-close')) closeModal(overlay);
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.cart-modal-overlay').forEach(function (m) {
        if (m.style.display === 'flex') closeModal(m);
      });
    }
  });

  // Телефонная маска
  function phoneMask(el) {
    el.addEventListener('input', function () {
      var d = el.value.replace(/\D/g, '');
      if (d.startsWith('8')) d = '7' + d.slice(1);
      if (!d.startsWith('7')) d = '7' + d;
      d = d.slice(0, 11);
      var out = '+7';
      if (d.length > 1) out += ' (' + d.slice(1, 4);
      if (d.length >= 4) out += ') ' + d.slice(4, 7);
      if (d.length >= 7) out += '-' + d.slice(7, 9);
      if (d.length >= 9) out += '-' + d.slice(9, 11);
      el.value = out;
    });
  }

  // Email спецификации
  var emailBtn = document.getElementById('cart-email-spec-btn');
  if (emailBtn) emailBtn.addEventListener('click', function () { openModal('modal-email'); });
  var emailSubmit = document.getElementById('modal-email-submit');
  if (emailSubmit) emailSubmit.addEventListener('click', function () {
    var input = document.getElementById('modal-email-input');
    var err = document.getElementById('modal-email-error');
    var email = (input.value || '').trim();
    if (!email || email.indexOf('@') === -1) { err.textContent = 'Укажите корректный email'; err.style.display = ''; return; }
    err.style.display = 'none';
    emailSubmit.disabled = true; emailSubmit.textContent = 'Отправляем...';
    post(URLS.emailSpec, { email: email }).then(function (res) {
      emailSubmit.disabled = false; emailSubmit.textContent = 'Отправить';
      if (res.ok && res.data.success) {
        document.getElementById('modal-email-form').style.display = 'none';
        document.getElementById('modal-email-success').style.display = '';
      } else {
        err.textContent = (res.data && res.data.error) || 'Ошибка отправки'; err.style.display = '';
      }
    }).catch(function () {
      emailSubmit.disabled = false; emailSubmit.textContent = 'Отправить';
      err.textContent = 'Ошибка соединения'; err.style.display = '';
    });
  });

  // B2B счёт
  var invBtn = document.getElementById('cart-invoice-btn');
  if (invBtn) invBtn.addEventListener('click', function () { openModal('modal-invoice'); });
  var invPhone = document.getElementById('inv-phone');
  if (invPhone) phoneMask(invPhone);
  var invSubmit = document.getElementById('modal-invoice-submit');
  if (invSubmit) invSubmit.addEventListener('click', function () {
    var company = (document.getElementById('inv-company').value || '').trim();
    var inn = (document.getElementById('inv-inn').value || '').trim();
    var email = (document.getElementById('inv-email').value || '').trim();
    var phone = (document.getElementById('inv-phone').value || '').trim();
    var comment = (document.getElementById('inv-comment').value || '').trim();
    var err = document.getElementById('modal-invoice-error');
    if (!company || !inn || (!email && !phone)) {
      err.textContent = 'Заполните компанию, ИНН и контакт'; err.style.display = ''; return;
    }
    err.style.display = 'none';
    invSubmit.disabled = true; invSubmit.textContent = 'Отправляем...';
    post(URLS.requestInvoice, { company: company, inn: inn, email: email, phone: phone, comment: comment })
      .then(function (res) {
        invSubmit.disabled = false; invSubmit.textContent = 'Отправить заявку';
        if (res.ok && res.data.success) {
          document.getElementById('modal-invoice-form').style.display = 'none';
          document.getElementById('modal-invoice-success').style.display = '';
        } else {
          err.textContent = (res.data && res.data.error) || 'Ошибка'; err.style.display = '';
        }
      }).catch(function () {
        invSubmit.disabled = false; invSubmit.textContent = 'Отправить заявку';
        err.textContent = 'Ошибка соединения'; err.style.display = '';
      });
  });

  // Первичный пересчёт
  recalcSidebar();
})();
