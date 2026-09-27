(function () {
  'use strict';

  function facetRow(item) {
    var row = document.createElement('li');
    var link = document.createElement('a');
    link.href = item.url;
    if (item.selected) {
      row.appendChild(document.createTextNode(item.text + ' (' + item.count + ') '));
      var icon = document.createElement('span');
      icon.className = 'glyphicon glyphicon-remove';
      icon.setAttribute('aria-hidden', 'true');
      link.appendChild(icon);
      link.setAttribute('aria-label', 'Remove facet ' + item.text);
      row.appendChild(link);
    } else {
      link.textContent = item.text;
      row.appendChild(link);
      row.appendChild(document.createTextNode(' (' + item.count + ')'));
    }
    return row;
  }

  function prepareFacet(dialog) {
    var name = dialog.dataset.facetName;
    var values = JSON.parse(document.getElementById('facet-data-' + name).textContent);
    var input = dialog.querySelector('input');
    var list = dialog.querySelector('.modal-body ul');
    var controls = dialog.querySelectorAll('[data-facet-action]');
    var page = 1;
    var sort = 'count';
    var pageCount = 1;

    function render() {
      var query = input.value.toUpperCase();
      var selected = values.filter(function (item) { return item.text.toUpperCase().includes(query); });
      selected.sort(function (a, b) {
        if (sort === 'count') return b.count - a.count;
        var left = a.text.toUpperCase();
        var right = b.text.toUpperCase();
        return left < right ? -1 : left > right ? 1 : 0;
      });
      pageCount = Math.max(1, Math.ceil(selected.length / 20));
      page = Math.max(1, Math.min(page, pageCount));
      list.replaceChildren();
      selected.slice((page - 1) * 20, page * 20).forEach(function (item) { list.appendChild(facetRow(item)); });
      dialog.querySelector('.facet-page-status').textContent = selected.length + ' values; page ' + page + ' of ' + pageCount;
      controls.forEach(function (control) {
        var action = control.dataset.facetAction;
        var disabled = (action === 'previous' && page === 1) || (action === 'next' && page === pageCount);
        control.classList.toggle('disabled', disabled);
        control.setAttribute('aria-disabled', String(disabled));
        control.tabIndex = disabled ? -1 : 0;
        if (action === 'alphabetical' || action === 'count') {
          control.classList.toggle('active', action === sort);
          control.setAttribute('aria-pressed', String(action === sort));
        }
      });
    }
    controls.forEach(function (control) {
      control.addEventListener('click', function (event) {
        event.preventDefault();
        if (control.getAttribute('aria-disabled') === 'true') return;
        var action = control.dataset.facetAction;
        if (action === 'previous') page -= 1;
        else if (action === 'next') page += 1;
        else { sort = action; page = 1; }
        render();
      });
      control.addEventListener('keydown', function (event) {
        if (event.key === ' ') { event.preventDefault(); control.click(); }
      });
    });
    input.addEventListener('input', function () { page = 1; render(); });
    window.jQuery(dialog).on('shown.bs.modal', function () { render(); input.focus(); });
    render();
  }

  function preparePreview(link, index) {
    var content = document.getElementById(link.dataset.matchContent);
    var tooltip;
    function hide() {
      if (tooltip) tooltip.remove();
      tooltip = null;
      link.removeAttribute('aria-describedby');
    }
    function show(event) {
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
      left = Math.max(8, Math.min(left, window.innerWidth - tooltip.offsetWidth - 8));
      if (top + tooltip.offsetHeight > window.innerHeight && box.top >= tooltip.offsetHeight + 15) top = box.top - tooltip.offsetHeight - 15;
      tooltip.style.left = left + 'px';
      tooltip.style.top = top + 'px';
      link.setAttribute('aria-describedby', tooltip.id);
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
