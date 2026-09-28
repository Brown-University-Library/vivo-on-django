(function () {
  'use strict';

  var sourceElement = document.getElementById('network-data');
  if (!sourceElement || !window.d3) return;
  var page = JSON.parse(sourceElement.textContent);
  var source = page.source;
  var svg = d3.select('#svgElement');
  var tooltip = document.getElementById('tooltip');
  var scope = page.type === 'PEOPLE' ? 1 : 1;
  var simulation = null;
  var rootUri = 'http://vivo.brown.edu/individual/' + page.id;
  var linkedIds = new Set();
  source.links.forEach(function (link) {
    linkedIds.add(link.source);
    linkedIds.add(link.target);
  });
  var allNodes = source.nodes.filter(function (node) { return linkedIds.has(node.id); });
  var allLinks = source.links.slice();
  var rootIds = new Set([rootUri, page.id]);
  var directIds = new Set();

  allLinks.forEach(function (link) {
    if (rootIds.has(link.source)) directIds.add(link.target);
    if (rootIds.has(link.target)) directIds.add(link.source);
  });
  allNodes.forEach(function (node) {
    if (page.type === 'PEOPLE') {
      node.localLevel = rootIds.has(node.id) ? 0 : (directIds.has(node.id) ? 1 : 2);
    } else {
      node.localLevel = Number.isInteger(node.level) ? node.level : 1;
    }
  });

  var groups = Array.from(new Set(allNodes.map(function (node) { return node.group || 'N/A'; }))).sort();
  var top = groups.indexOf(page.name);
  if (top !== -1) groups.unshift(groups.splice(top, 1)[0]);
  var colors = d3.scaleOrdinal(d3.schemeCategory20).domain(groups);
  var headingColor = colors(page.type === 'PEOPLE' ? (groups[0] || 'N/A') : page.name);
  document.querySelector('.researcherName').style.borderLeftColor = headingColor;
  var subtitle = document.querySelector('.facultyTitle');
  if (subtitle) subtitle.style.borderLeftColor = headingColor;
  if (page.updated) {
    var date = new Date(page.updated + 'T00:00:00Z');
    if (!Number.isNaN(date.getTime())) {
      var formatted = date.toLocaleDateString('en-US', {timeZone: 'UTC'});
      var calculated = document.getElementById('calculatedInfo');
      var organizationDate = document.getElementById('txtLastUpdated');
      if (calculated) calculated.textContent = 'The ' + (page.kind === 'coauthors' ? 'coauthor' : 'collaborator') +
        ' network for this researcher was calculated on ' + formatted + '.';
      if (organizationDate) organizationDate.textContent = formatted;
    }
  }
  var missingDate = document.getElementById('txtLastUpdated');
  if (missingDate && !missingDate.textContent) missingDate.textContent = '(not available)';
  var legend = document.getElementById('legendList');
  groups.forEach(function (group) {
    var row = document.createElement('li');
    var swatch = document.createElement('span');
    swatch.style.backgroundColor = colors(group);
    row.appendChild(swatch);
    row.appendChild(document.createTextNode(group));
    legend.appendChild(row);
  });

  function updateScopeButtons() {
    [['showLess', 1], ['showMore', 2], ['showLevel0', 0], ['showLevel1', 1]].forEach(function (entry) {
      var button = document.getElementById(entry[0]);
      if (!button) return;
      button.classList.toggle('btn-info', scope === entry[1]);
      button.classList.toggle('btn-default', scope !== entry[1]);
    });
  }

  function draw() {
    if (simulation) simulation.stop();
    svg.selectAll('*').remove();
    var nodes = allNodes.filter(function (node) { return node.localLevel <= scope; }).map(function (node) {
      return Object.assign({}, node);
    });
    var visible = new Set(nodes.map(function (node) { return node.id; }));
    var links = allLinks.filter(function (link) {
      return visible.has(link.source) && visible.has(link.target);
    }).map(function (link) { return Object.assign({}, link); });
    updateScopeButtons();
    if (!nodes.length) return;

    var edges = svg.append('g').selectAll('line').data(links).enter().append('line')
      .attr('stroke', '#ccc').attr('stroke-width', 1);
    var people = svg.append('g').selectAll('g').data(nodes).enter().append('g')
      .style('cursor', 'pointer');
    people.append('circle')
      .attr('r', function (node) { return node.localLevel === 0 ? 15 : (node.localLevel === 1 ? 11 : 6); })
      .attr('fill', function (node) { return colors(node.group || 'N/A'); });
    people.append('text').attr('class', 'node-text')
      .attr('font-size', function (node) { return node.localLevel === 0 ? 12 : 8; })
      .attr('font-weight', function (node) { return node.localLevel === 0 ? 'bold' : 'normal'; })
      .text(function (node) { return node.name || ''; });
    people.selectAll('text').classed('hidden', !document.getElementById('showLabels').checked);

    people.on('mouseover', function (node) {
      if (!document.getElementById('showDetails').checked) return;
      tooltip.textContent = (node.name || '') + (node.group ? ' — ' + node.group : '');
      tooltip.style.left = (d3.event.clientX + 16) + 'px';
      tooltip.style.top = (d3.event.clientY - 20) + 'px';
      tooltip.classList.remove('hidden');
    }).on('mouseout', function () { tooltip.classList.add('hidden'); });
    people.on('click', function (node) {
      if (page.type === 'PEOPLE' && rootIds.has(node.id)) return;
      var shortId = node.id.split('/').pop();
      if (!/^[A-Za-z0-9_-]{1,80}$/.test(shortId)) return;
      window.location.assign(page.type === 'PEOPLE'
        ? '/display/' + shortId + '/viz/' + (page.kind === 'coauthors' ? 'coauthor' : 'collab')
        : '/display/' + shortId + '/');
    });

    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(function (node) { return node.id; })
        .distance(document.getElementById('forceToFit').checked ? 45 : 100).strength(0.1))
      .force('charge', d3.forceManyBody())
      .force('center', d3.forceCenter(480, 350));
    people.call(d3.drag()
      .on('start', function (node) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        node.fx = node.x;
        node.fy = node.y;
      })
      .on('drag', function (node) { node.fx = d3.event.x; node.fy = d3.event.y; })
      .on('end', function () { simulation.alphaTarget(0); }));
    simulation.on('tick', function () {
      edges.attr('x1', function (link) { return link.source.x; })
        .attr('y1', function (link) { return link.source.y; })
        .attr('x2', function (link) { return link.target.x; })
        .attr('y2', function (link) { return link.target.y; });
      people.attr('transform', function (node) { return 'translate(' + node.x + ',' + node.y + ')'; });
    });
  }

  [['showLess', 1], ['showMore', 2], ['showLevel0', 0], ['showLevel1', 1]].forEach(function (entry) {
    var button = document.getElementById(entry[0]);
    if (button) button.addEventListener('click', function () { scope = entry[1]; draw(); });
  });
  document.getElementById('showLabels').addEventListener('change', function () {
    svg.selectAll('.node-text').classed('hidden', !this.checked);
  });
  document.getElementById('forceToFit').addEventListener('change', function () {
    var url = new URL(window.location.href);
    if (this.checked) url.searchParams.set('fit', '1');
    else url.searchParams.delete('fit');
    window.location.assign(url.toString());
  });

  function svgCode() {
    var image = document.getElementById('svgElement').cloneNode(true);
    image.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    image.querySelectorAll('.hidden').forEach(function (node) { node.remove(); });
    return new XMLSerializer().serializeToString(image);
  }
  document.getElementById('embedHtml').addEventListener('click', function () {
    document.getElementById('embedHtmlText').value = svgCode();
    document.getElementById('embedHtmlDiv').classList.remove('hidden');
  });
  document.getElementById('downloadPng').addEventListener('click', function () {
    var status = document.getElementById('downloadStatus');
    status.textContent = 'Preparing image…';
    status.classList.remove('hidden');
    var image = new Image();
    var svgUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgCode());
    image.onload = function () {
      var canvas = document.createElement('canvas');
      canvas.width = 960;
      canvas.height = 700;
      var context = canvas.getContext('2d');
      context.fillStyle = '#fff';
      context.fillRect(0, 0, 960, 700);
      context.drawImage(image, 0, 0);
      canvas.toBlob(function (blob) {
        if (!blob) {
          status.textContent = 'The image could not be created.';
          return;
        }
        var pngUrl = URL.createObjectURL(blob);
        var download = document.createElement('a');
        download.href = pngUrl;
        download.download = page.kind + '_' + page.id + '.png';
        document.body.appendChild(download);
        download.click();
        download.remove();
        status.textContent = 'Image download started.';
        setTimeout(function () { URL.revokeObjectURL(pngUrl); }, 1000);
      }, 'image/png');
    };
    image.onerror = function () { status.textContent = 'The image could not be created.'; };
    image.src = svgUrl;
  });
  draw();
}());
