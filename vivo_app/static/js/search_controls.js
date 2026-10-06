(function () {
  'use strict';

  function facetRow(item) {
    var row = document.createElement('li');
    var link = document.createElement('a');
    var label = document.createElement('template');
    // Read rendered label text without changing the raw filter value or URL.
    label.innerHTML = item.text;
    var text = label.content.textContent;
    link.href = item.url;
    if (item.selected) {
      row.appendChild(document.createTextNode(text + ' (' + item.count + ') '));
      var icon = document.createElement('span');
      icon.className = 'glyphicon glyphicon-remove';
      icon.setAttribute('aria-hidden', 'true');
      link.appendChild(icon);
      link.setAttribute('aria-label', 'Remove facet ' + text);
      row.appendChild(link);
    } else {
      link.textContent = text;
      row.appendChild(link);
      row.appendChild(document.createTextNode(' (' + item.count + ')'));
    }
    return row;
  }

  function prepareFacet(dialog) {
    var name = dialog.dataset.facetName;
    var facetUrl = dialog.dataset.facetUrl;
    var values = JSON.parse(document.getElementById('facet-data-' + name).textContent);
    var input = dialog.querySelector('input');
    var list = dialog.querySelector('.modal-body ul');
    var loadStatus = dialog.querySelector('.facet-load-status');
    var controls = dialog.querySelectorAll('[data-facet-action]');
    var page = 1;
    var sort = 'count';
    var pageCount = 1;
    var loaded = !facetUrl;
    var loading = false;

    function render() {
      var query = input.value.toUpperCase();
      values.sort(function (a, b) {
        if (sort === 'count') return b.count - a.count;
        var left = a.text.toUpperCase();
        var right = b.text.toUpperCase();
        return left < right ? -1 : left > right ? 1 : 0;
      });
      var selected = values.filter(function (item) { return item.text.toUpperCase().includes(query); });
      pageCount = Math.ceil(selected.length / 20);
      list.replaceChildren();
      // Preserve the reference pager's keyboard behavior at either boundary.
      for (var index = (page - 1) * 20; index < Math.min(page * 20, selected.length); index += 1) {
        list.appendChild(facetRow(selected[index]));
      }
      dialog.querySelector('.facet-page-status').textContent = selected.length + ' values; page ' + page + ' of ' + pageCount;
      controls.forEach(function (control) {
        var action = control.dataset.facetAction;
        var disabled = (action === 'previous' && page === 1) || (action === 'next' && page >= pageCount);
        control.classList.toggle('disabled', disabled);
        if (action === 'alphabetical' || action === 'count') {
          control.classList.toggle('active', action === sort);
          control.setAttribute('aria-pressed', String(action === sort));
        }
      });
    }
    controls.forEach(function (control) {
      control.addEventListener('click', function (event) {
        event.preventDefault();
        var action = control.dataset.facetAction;
        if (action === 'previous') page -= 1;
        else if (action === 'next') page += 1;
        else { sort = action; page = 1; }
        render();
      });
    });
    input.addEventListener('input', function () { page = 1; render(); });
    window.jQuery(dialog).on('shown.bs.modal', function () {
      input.focus();
      if (loaded) { render(); return; }
      if (loading) return;
      loading = true;
      loadStatus.textContent = 'Loading...';
      window.fetch(facetUrl, { credentials: 'same-origin' })
        .then(function (response) {
          if (!response.ok) throw new Error('Facet request failed');
          return response.json();
        })
        .then(function (rows) {
          if (!Array.isArray(rows)) throw new Error('Invalid facet response');
          values = rows.map(function (item) {
            if (!item || typeof item.text !== 'string' || !Number.isInteger(item.count) ||
                typeof item.add_url !== 'string' ||
                (item.remove_url !== null && typeof item.remove_url !== 'string')) {
              throw new Error('Invalid facet value');
            }
            return { text: item.text, count: item.count, selected: item.remove_url !== null,
              url: item.remove_url || item.add_url };
          });
          loaded = true;
          loadStatus.textContent = '';
          render();
        })
        .catch(function () { loadStatus.textContent = 'Could not retrieve facet information. Reopen to try again.'; })
        .finally(function () { loading = false; });
    });
    if (loaded) render();
  }

  function preparePreview(link, index) {
    var content = document.getElementById(link.dataset.matchContent);
    var tooltip;
    function hide() {
      if (tooltip) window.jQuery(tooltip).fadeOut(function () { this.remove(); });
      tooltip = null;
      link.removeAttribute('aria-describedby');
    }
    function show() {
      hide();
      tooltip = document.createElement('div');
      tooltip.className = 'prepared-match-tooltip ui-tooltip';
      tooltip.id = 'search-match-tooltip-' + index;
      tooltip.setAttribute('role', 'tooltip');
      var body = document.createElement('div');
      body.className = 'ui-tooltip-content';
      body.appendChild(content.content.cloneNode(true));
      tooltip.appendChild(body);
      document.body.appendChild(tooltip);
      var box = link.getBoundingClientRect();
      var left = box.left;
      var top = box.top + window.jQuery(link).outerHeight() + 15;
      // Match the dimensions and flip rules used by the reference jQuery UI tooltip.
      var width = window.jQuery(tooltip).outerWidth();
      var height = window.jQuery(tooltip).outerHeight();
      var flippedLeft = box.right - width;
      var overRight = left + width - window.innerWidth;
      if (left < 0 && (flippedLeft + width < window.innerWidth || flippedLeft + width - window.innerWidth < -left)) {
        left = flippedLeft;
      } else if (overRight > 0 && (flippedLeft > 0 || Math.abs(flippedLeft) < overRight)) {
        left = flippedLeft;
      }
      left = Math.max(0, Math.min(left, window.innerWidth - width));
      var flippedTop = box.top - height - 15;
      var overBottom = top + height - window.innerHeight;
      if (top < 0 && (flippedTop + height < window.innerHeight || flippedTop + height - window.innerHeight < -top)) {
        top = flippedTop;
      } else if (overBottom > 0 && (flippedTop > 0 || Math.abs(flippedTop) < overBottom)) {
        top = flippedTop;
      }
      window.jQuery(tooltip).offset({ left: left + window.scrollX, top: top + window.scrollY });
      link.setAttribute('aria-describedby', tooltip.id);
      window.jQuery(tooltip).hide().fadeIn();
    }
    link.addEventListener('mouseenter', show);
    link.addEventListener('focus', show);
    link.addEventListener('mouseleave', hide);
    link.addEventListener('blur', hide);
    link.addEventListener('keydown', function (event) { if (event.key === 'Escape') hide(); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.prepared-facet-dialog').forEach(prepareFacet);
    document.querySelectorAll('[data-match-content]').forEach(preparePreview);
  });
})();
