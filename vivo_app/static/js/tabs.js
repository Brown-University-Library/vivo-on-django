(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  function $(selector, root) {
    return (root || document).querySelector(selector);
  }

  function $all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function show(el) {
    if (!el) return;
    el.style.display = '';
    el.removeAttribute('aria-hidden');
  }

  function hide(el) {
    if (!el) return;
    el.style.display = 'none';
    el.setAttribute('aria-hidden', 'true');
  }

  function setActive(btns, activeBtn) {
    btns.forEach(function (b) {
      b.classList.remove('active');
      b.removeAttribute('aria-current');
    });
    if (activeBtn) {
      activeBtn.classList.add('active');
      activeBtn.setAttribute('aria-current', 'true');
    }
  }

  ready(function () {
    var panel = $('#section_overview');
    var tabButtons = $('#tabButtons');
    if (!panel || !tabButtons) return; // Only run on people profile pages with tabs

    var sections = $all('#section_overview .tabFinder');
    var btns = $all('#tabButtons a[id^="tab"][id$="Btn"]');

    function showOnly(sectionId) {
      sections.forEach(function (s) { hide(s); });
      var target = $('#' + sectionId);
      if (target) show(target);
    }

    function showAll() {
      sections.forEach(function (s) { show(s); });
    }

    function activateFromHash() {
      var wanted = window.location.hash.slice(1) || 'Overview';
      var active = btns.find(function (b) { return b.getAttribute('href') === '#' + wanted; });
      var target = sections.find(function (s) { return s.id === 'tab' + wanted; });
      if (wanted === 'All') showAll();
      else if (target) showOnly(target.id);
      else if (['Publications', 'Research', 'Background', 'Affiliations', 'Teaching'].indexOf(wanted) !== -1) {
        showOnly('tab' + wanted);
      }
      else {
        showOnly('tabOverview');
        active = $('#tabOverviewBtn');
      }
      setActive(btns, active);
      if (wanted === 'Overview' && window.location.hash) {
        history.replaceState(null, '', '#');
      }
    }
    activateFromHash();
    window.addEventListener('hashchange', activateFromHash);
    btns.forEach(function (btn) {
      btn.addEventListener('click', function (ev) {
        ev.preventDefault();
        history.replaceState(null, '', btn.getAttribute('href'));
        activateFromHash();
      });
    });
  });
})();

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    var buttons = document.querySelectorAll('button[data-publication-type]');
    var rows = document.querySelectorAll('tr[data-publication-type]');
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var type = button.dataset.publicationType;
        rows.forEach(function (row) {
          var citation = row.querySelector('td');
          if (citation) {
            citation.hidden = type !== 'all' && row.dataset.publicationType !== type;
          }
        });
        buttons.forEach(function (other) {
          other.classList.toggle('active', other === button);
          other.setAttribute('aria-pressed', String(other === button));
        });
      });
    });
  });
})();
