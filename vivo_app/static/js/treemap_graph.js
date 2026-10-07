(function () {
  'use strict';

  var sourceElement = document.getElementById('treemap-data');
  if (!sourceElement || !window.d3) return;
  var page = JSON.parse(sourceElement.textContent);
  var source = page.source;
  var rootIds = new Set([page.id, 'http://vivo.brown.edu/individual/' + page.id]);
  var byId = new Map(source.nodes.map(function (node) { return [node.id, node]; }));
  var children = new Map();
  source.links.forEach(function (link) {
    var otherId = rootIds.has(link.source) ? link.target : (rootIds.has(link.target) ? link.source : null);
    if (!otherId) return;
    var node = byId.get(otherId);
    if (!node) return;
    var current = children.get(otherId);
    if (!current) {
      current = {id: otherId, name: node.name || otherId, group: node.group || 'N/A', size: 0};
      children.set(otherId, current);
    }
    current.size += Number(link.weight) || 1;
  });
  if (!children.size) {
    document.getElementById('errorMsg').classList.remove('hidden');
    return;
  }

  var allGroups = Array.from(new Set(source.nodes.map(function (node) { return node.group || 'N/A'; }))).sort();
  var colors = d3.scaleOrdinal(d3.schemeCategory20).domain(allGroups);
  var rootNode = source.nodes.find(function (node) { return rootIds.has(node.id); });
  var headingColor = colors(rootNode ? (rootNode.group || 'N/A') : allGroups[0]);
  document.querySelector('.researcherName').style.borderLeftColor = headingColor;
  var subtitle = document.querySelector('.facultyTitle');
  if (subtitle) subtitle.style.borderLeftColor = headingColor;
  if (page.updated) {
    var date = new Date(page.updated + 'T00:00:00Z');
    if (!Number.isNaN(date.getTime())) {
      document.getElementById('calculatedInfo').textContent =
        'The coauthor treemap for this researcher was calculated on ' +
        date.toLocaleDateString('en-US', {timeZone: 'UTC'}) + '.';
    }
  }

  var root = d3.hierarchy({name: page.name, children: Array.from(children.values())})
    .sum(function (node) { return node.size || 0; })
    .sort(function (left, right) { return right.height - left.height || right.value - left.value; });
  d3.treemap().tile(d3.treemapResquarify).size([900, 700]).round(true).paddingInner(1)(root);
  var svg = d3.select('#svgElement');
  var cell = svg.selectAll('g').data(root.leaves()).enter().append('g')
    .attr('transform', function (node) { return 'translate(' + node.x0 + ',' + node.y0 + ')'; });
  cell.append('rect')
    .attr('id', function (node) { return 'Publications with ' + node.data.name; })
    .attr('width', function (node) { return node.x1 - node.x0; })
    .attr('height', function (node) { return node.y1 - node.y0; })
    .attr('fill', function (node) { return colors(node.data.group); });
  cell.append('clipPath').attr('id', function (node) { return 'clip-Publications with ' + node.data.name; });
  cell.append('text').attr('clip-path', function (node) { return 'url(#clip-Publications with ' + node.data.name + ')'; })
    .selectAll('tspan')
    .data(function (node) { return node.data.name.split(/(?=[A-Z][^A-Z])/g); })
    .enter().append('tspan').attr('x', 4)
    .attr('y', function (part, index) { return 13 + index * 10; })
    .text(function (part) { return part; });
  cell.append('title').text(function (node) {
    return 'Publications with ' + node.data.name + '\n' + d3.format(',d')(node.value);
  });
  cell.on('click', function (node) {
    var shortId = node.data.id.split('/').pop();
    if (/^[A-Za-z0-9_-]{1,80}$/.test(shortId)) {
      var destination = new URL(window.location.href);
      destination.pathname = destination.pathname.replace('/display/' + page.id + '/viz/', '/display/' + shortId + '/viz/');
      window.location.assign(destination.toString());
    }
  }).on('mouseover', function () {
    d3.select(this).select('rect').attr('stroke', 'blue').attr('stroke-width', 2);
  }).on('mouseout', function () {
    d3.select(this).select('rect').attr('stroke', '').attr('stroke-width', 0);
  });
  var legend = document.getElementById('legendList');
  Array.from(new Set(Array.from(children.values()).map(function (node) { return node.group; }))).sort()
    .forEach(function (group) {
      var row = document.createElement('li');
      var swatch = document.createElement('span');
      swatch.style.backgroundColor = colors(group);
      swatch.textContent = '\u00a0\u00a0\u00a0\u00a0';
      row.appendChild(swatch);
      row.appendChild(document.createTextNode('\u00a0' + group));
      legend.appendChild(row);
    });

  function svgCode() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700">\r\n' +
      document.getElementById('svgElement').innerHTML + '\r\n</svg>';
  }
  document.getElementById('embedHtml').addEventListener('click', function () {
    document.getElementById('embedHtmlText').value = '<svg width="900" height="700">\r\n' +
      document.getElementById('svgElement').innerHTML + '\r\n</svg>';
    document.getElementById('embedHtmlDiv').classList.remove('hidden');
    $('html, body').animate({scrollTop: $(document).height() - $(window).height()}, 1400, 'swing');
  });
  document.getElementById('downloadPng').addEventListener('click', function () {
    var status = document.getElementById('downloadStatus');
    status.textContent = 'Preparing image…';
    var image = new Image();
    image.onload = function () {
      var canvas = document.createElement('canvas');
      canvas.width = 900;
      canvas.height = 700;
      var context = canvas.getContext('2d');
      context.fillStyle = '#fff';
      context.fillRect(0, 0, 900, 700);
      context.drawImage(image, 0, 0);
      canvas.toBlob(function (blob) {
        if (!blob) {
          status.textContent = 'The image could not be created.';
          return;
        }
        var url = URL.createObjectURL(blob);
        var download = document.createElement('a');
        download.href = url;
        download.download = 'coauthors_' + page.id + '.png';
        document.body.appendChild(download);
        download.click();
        download.remove();
        status.textContent = 'Image download started.';
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      }, 'image/png');
    };
    image.onerror = function () { status.textContent = 'The image could not be created.'; };
    image.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgCode());
  });
}());
