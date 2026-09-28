(function () {
  'use strict';

  var dataElement = document.getElementById('research-chart-data');
  if (!dataElement || !window.d3) return;
  var data = JSON.parse(dataElement.textContent);
  var svg = d3.select('#svgElement');
  var people = data.nodes[0].slice().sort(function (a, b) { return b.nodeValue - a.nodeValue; });
  var areas = data.nodes[1].slice().sort(function (a, b) { return b.nodeValue - a.nodeValue; });
  if (!data.links.length) {
    document.getElementById('errorMsg').classList.remove('hidden');
    return;
  }
  var height = Math.max(people.length, areas.length) > 30 ? 1700 : 700;
  svg.attr('height', height).attr('viewBox', '0 0 960 ' + height);
  var totals = [people, areas].map(function (nodes) {
    return d3.sum(nodes, function (node) { return node.nodeValue; });
  });
  var maxTotal = d3.max(totals) || 1;
  var gap = 15;
  var scale = (height - gap * Math.max(people.length, areas.length)) / maxTotal;
  var colors = d3.scaleOrdinal(d3.schemeCategory20);
  var positions = new Map();
  [people, areas].forEach(function (nodes, side) {
    var y = 0;
    nodes.forEach(function (node) {
      positions.set(node.id, {x: side ? 711 : 0, y: y, height: Math.max(1, node.nodeValue * scale), side: side});
      y += node.nodeValue * scale + gap;
    });
  });
  var outgoing = new Map();
  var incoming = new Map();
  data.links.forEach(function (link) {
    var source = positions.get(link.source);
    var target = positions.get(link.target);
    if (!source || !target) return;
    var start = (outgoing.get(link.source) || 0) + 0.5;
    var end = (incoming.get(link.target) || 0) + 0.5;
    outgoing.set(link.source, start + 0.5);
    incoming.set(link.target, end + 0.5);
    var y0 = source.y + start * scale;
    var y1 = target.y + end * scale;
    svg.append('path').attr('class', 'link')
      .attr('d', 'M 213,' + y0 + ' C 462,' + y0 + ' 462,' + y1 + ' 711,' + y1)
      .attr('fill', 'none').attr('stroke', colors(link.target))
      .attr('stroke-width', Math.max(1, scale)).attr('stroke-opacity', 0.45)
      .append('title').text('Shared research area');
  });
  [people, areas].forEach(function (nodes) {
    nodes.forEach(function (node) {
      var position = positions.get(node.id);
      var group = svg.append('g').attr('class', 'node');
      group.append('rect').attr('x', position.x).attr('y', position.y)
        .attr('width', 213).attr('height', position.height)
        .attr('fill', position.side ? colors(node.id) : 'lightgray');
      group.append('text').attr('x', position.x + 4).attr('y', position.y + 15)
        .attr('class', 'node-text').text(node.display);
      group.append('title').text(node.areas ? 'Research areas: ' + node.areas : node.display);
    });
  });
  document.getElementById('embedHtml').addEventListener('click', function () {
    var image = document.getElementById('svgElement').cloneNode(true);
    image.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    document.getElementById('embedHtmlText').value = new XMLSerializer().serializeToString(image);
    document.getElementById('embedHtmlDiv').classList.remove('hidden');
  });
}());
