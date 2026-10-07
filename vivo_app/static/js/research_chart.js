(function () {
  'use strict';

  var dataElement = document.getElementById('research-chart-data');
  if (!dataElement || !window.d3) return;
  var data = JSON.parse(dataElement.textContent);
  var svg = d3.select('#svgElement');
  if (!data.links.length || !data.nodes[1].length) {
    document.getElementById('errorMsg').classList.remove('hidden');
  } else {
    draw();
  }

  // Preserve the reference's cubic basis segments, including its repeated ends.
  function basis(points) {
    var x = [points[0][0], points[0][0], points[0][0], points[1][0]];
    var y = [points[0][1], points[0][1], points[0][1], points[1][1]];
    var path = ['M', points[0][0], ',', points[0][1]];
    basisSegment(path, x, y);
    points.slice(2).concat([points[points.length - 1], points[points.length - 1]]).forEach(function (point) {
      x.shift(); x.push(point[0]);
      y.shift(); y.push(point[1]);
      basisSegment(path, x, y);
    });
    return path.join('');
  }

  function weighted(coefficients, values) {
    return coefficients[0] * values[0] + coefficients[1] * values[1] +
      coefficients[2] * values[2] + coefficients[3] * values[3];
  }

  function basisSegment(path, x, y) {
    var a = [0, 2 / 3, 1 / 3, 0];
    var b = [0, 1 / 3, 2 / 3, 0];
    var c = [0, 1 / 6, 2 / 3, 1 / 6];
    path.push('C', weighted(a, x), ',', weighted(a, y), ',', weighted(b, x), ',', weighted(b, y),
      ',', weighted(c, x), ',', weighted(c, y));
  }

  function draw() {
    var height = Math.max(data.nodes[0].length, data.nodes[1].length) > 30 ? 1700 : 700;
    svg.attr('height', height);
    var colors = d3.scaleOrdinal(d3.schemeCategory20);
    var nodesById = new Map();
    var firstResearchArea = data.nodes[1][0].id;
    data.nodes.forEach(function (nodes) {
      nodes.forEach(function (node) {
        node.links = [];
        node.incoming = [];
        node.nodeValue = node.nodeValue || 0;
        nodesById.set(node.id, node);
      });
    });
    data.links.forEach(function (link) {
      nodesById.get(link.source).links.push(link);
      nodesById.get(link.target).incoming.push(link);
    });
    data.nodes.forEach(function (nodes) {
      var total = 0;
      nodes.sort(function (a, b) { return d3.descending(a.nodeValue, b.nodeValue); });
      nodes.forEach(function (node, index) {
        node.order = index;
        node.offsetValue = total;
        total += node.nodeValue;
        ['links', 'incoming'].forEach(function (key) {
          var offset = 0;
          node[key].sort(function (a, b) { return d3.descending(a.value, b.value); });
          node[key].forEach(function (link) {
            link[key === 'links' ? 'outOffset' : 'inOffset'] = offset;
            offset += link.value;
          });
        });
      });
    });
    var maxNodes = d3.max(data.nodes, function (nodes) { return nodes.length; });
    var maxValue = d3.max(data.nodes, function (nodes) {
      return d3.sum(nodes, function (node) { return node.nodeValue; });
    });
    var gapRatio = 0.7;
    var step = (960 + 960 / (data.nodes.length - 1)) / (data.nodes.length - gapRatio + 2 * gapRatio);
    var gapWidth = step * gapRatio;
    var bandWidth = step * (1 - gapRatio);
    // Match the reference's reciprocal multiplication before interpolation.
    var reciprocal = maxValue ? 1 / maxValue : 0;
    var rangeHeight = height - 15 * maxNodes;
    function y(value) { return rangeHeight * (value * reciprocal); }
    data.nodes.forEach(function (nodes, side) {
      var sideX = (gapWidth + side * step) - gapWidth;
      var time = svg.append('g').attr('class', 'time').attr('transform', 'translate(' + sideX + ',0)');
      var groups = time.selectAll('g.node').data(nodes).enter().append('g').attr('class', 'node');
      groups.append('rect').attr('fill', function (node) {
        return node.id >= firstResearchArea ? colors(node.id) : 'lightgray';
      }).attr('y', function (node, index) { return y(node.offsetValue) + index * 15; })
        .attr('width', bandWidth).attr('height', function (node) { return y(node.nodeValue); });
      groups.append('title').text(function (node) {
        if (node.id >= firstResearchArea) return node.nodeName;
        if (node.areas === '') return 'This researchas has not specified research areas.';
        return 'Research areas: ' + node.areas;
      });
      groups.append('text').attr('y', function (node, index) { return y(node.offsetValue) + index * 15 + 15; })
        .text(function (node) { return node.display; });
      groups.selectAll('path.link').data(function (node) { return node.incoming; }).enter().append('path')
        .attr('class', 'link').style('stroke', function (link) { return colors(link.target); })
        .style('stroke-width', function (link) { return y(link.value); })
        .attr('d', function (link) { return linkPath(link, true); })
        .on('mouseover', function () { d3.select(this).attr('class', 'link on'); })
        .on('mouseout', function () { d3.select(this).attr('class', 'link'); })
        .transition().duration(1500).attr('d', function (link) { return linkPath(link, false); });
    });

    function linkPath(link, start) {
      var source = nodesById.get(link.source);
      var target = nodesById.get(link.target);
      var sourceY = y(source.offsetValue) + source.order * 15 + y(link.outOffset) + y(link.value) / 2;
      var targetY = y(target.offsetValue) + target.order * 15 + y(link.inOffset) + y(link.value) / 2;
      // Keep the reference's subtraction order for its exported SVG coordinates.
      var startX = bandWidth - (bandWidth + gapWidth);
      return basis(start ? [[startX, sourceY], [startX, sourceY], [startX, sourceY], [startX, sourceY]] :
        [[startX, sourceY], [startX + gapWidth / 2, sourceY], [startX + gapWidth / 2, targetY], [0, targetY]]);
    }
  }

  document.getElementById('embedHtml').addEventListener('click', function () {
    document.getElementById('embedHtmlText').value = '<svg width="960" height="700">\r\n' +
      document.getElementById('svgElement').innerHTML + '\r\n</svg>';
    document.getElementById('embedHtmlDiv').classList.remove('hidden');
    $('html, body').animate({scrollTop: $(document).height() - $(window).height()}, 1400, 'swing');
  });
}());
