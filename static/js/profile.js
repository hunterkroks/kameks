// ──────────────────────────────────────────────────────────
// Личный кабинет — клиентская логика
// ──────────────────────────────────────────────────────────
(function () {
  function getCookie(name) {
    var v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }
  var csrftoken = getCookie('csrftoken');

  // ── Клиентский фильтр заказов (обзор) ──
  document.querySelectorAll('.filter-chips[data-filter-target]').forEach(function (chips) {
    var targetSel = chips.getAttribute('data-filter-target');
    var list = document.querySelector(targetSel);
    if (!list) return;
    var activeMap = ['pending', 'confirmed', 'paid', 'shipped'];

    chips.querySelectorAll('.filter-chip[data-filter]').forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.querySelectorAll('.filter-chip').forEach(function (c) { c.classList.remove('active'); });
        chip.classList.add('active');
        var f = chip.getAttribute('data-filter');
        list.querySelectorAll('.order-card').forEach(function (card) {
          var st = card.getAttribute('data-status');
          var show = (f === 'all')
            || (f === 'active' && activeMap.indexOf(st) !== -1)
            || (f === 'completed' && st === 'delivered')
            || (f === 'cancelled' && st === 'cancelled');
          card.style.display = show ? '' : 'none';
        });
      });
    });
  });

  // ── Клиентский поиск заказов (обзор) ──
  document.querySelectorAll('.order-search[data-search-target]').forEach(function (input) {
    var list = document.querySelector(input.getAttribute('data-search-target'));
    if (!list) return;
    var t;
    input.addEventListener('input', function () {
      clearTimeout(t);
      t = setTimeout(function () {
        var q = input.value.trim().toLowerCase();
        list.querySelectorAll('.order-card').forEach(function (card) {
          var hay = (card.getAttribute('data-number') + ' ' + card.getAttribute('data-desc')).toLowerCase();
          card.style.display = (!q || hay.indexOf(q) !== -1) ? '' : 'none';
        });
      }, 200);
    });
  });

  // ── Серверный поиск заказов (страница «Мои заказы») с debounce ──
  var serverSearch = document.getElementById('orders-server-search');
  if (serverSearch) {
    var st;
    serverSearch.addEventListener('input', function () {
      clearTimeout(st);
      st = setTimeout(function () {
        document.getElementById('orders-filter-form').submit();
      }, 500);
    });
  }

  // ── Уведомления: пометить прочитанным по клику ──
  document.querySelectorAll('.notif-item').forEach(function (item) {
    item.addEventListener('click', function (e) {
      if (!item.classList.contains('unread')) return;
      var id = item.getAttribute('data-id');
      if (!id) return;
      fetch('/accounts/profile/notifications/mark-read/' + id + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
      }).then(function (r) { return r.json(); }).then(function (data) {
        if (data.success) {
          item.classList.remove('unread');
          updateUnreadBadge(data.unread);
        }
      }).catch(function () {});
    });
  });

  function updateUnreadBadge(unread) {
    document.querySelectorAll('.menu-badge-red, .pb-badge-red').forEach(function (b) {
      if (unread > 0) {
        b.textContent = b.classList.contains('pb-badge-red') ? (unread + ' новых') : unread;
      } else {
        b.style.display = 'none';
      }
    });
  }
})();
