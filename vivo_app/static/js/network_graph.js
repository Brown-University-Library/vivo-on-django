(function () {
  'use strict';

  var sourceElement = document.getElementById('network-data');
  if (!sourceElement || !window.d3) return;
  var page = JSON.parse(sourceElement.textContent);
  var source = page.source;
  var personNetwork = page.type === 'PEOPLE' && !page.empty_network;
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
  var allNodes = personNetwork ? source.nodes.slice() : source.nodes.filter(function (node) { return linkedIds.has(node.id); });
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
  var rootNode = allNodes.find(function (node) { return rootIds.has(node.id); });
  var headingColor = colors(page.type === 'PEOPLE' ? (rootNode ? rootNode.group || 'N/A' : groups[0] || 'N/A') : page.name);
  if (!page.empty_network) document.querySelector('.researcherName').style.borderLeftColor = headingColor;
  var subtitle = document.querySelector('.facultyTitle');
  if (subtitle && !page.empty_network) subtitle.style.borderLeftColor = headingColor;
  if (page.updated && !page.empty_network) {
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
  function updateLegend(nodes) {
    legend.textContent = '';
    var visibleGroups = personNetwork
      ? Array.from(new Set(nodes.map(function (node) { return node.group || 'N/A'; }))).sort() : groups;
    visibleGroups.forEach(function (group) {
      var row = document.createElement('li');
      var swatch = document.createElement('span');
      swatch.style.backgroundColor = colors(group);
      if (personNetwork || page.type !== 'PEOPLE') swatch.textContent = '\u00a0\u00a0\u00a0\u00a0';
      row.appendChild(swatch);
      row.appendChild(document.createTextNode((personNetwork || page.type !== 'PEOPLE' ? '\u00a0' : '') + group));
      legend.appendChild(row);
    });
  }

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
      return personNetwork ? node : Object.assign({}, node);
    });
    var visible = new Set(nodes.map(function (node) { return node.id; }));
    var links = allLinks.filter(function (link) {
      return visible.has(link.source) && visible.has(link.target);
    }).map(function (link) { return Object.assign({}, link); });
    updateScopeButtons();
    updateLegend(nodes);
    if (page.empty_network || !nodes.length) return;

    var edges = svg.selectAll('line').data(links).enter().append('line');
    edges.style('stroke', '#ccc').style('stroke-width', 1);
    var people = svg.selectAll('g').data(nodes).enter().append('g');
    var circles = people.append('circle')
      .attr('r', function (node) { return node.localLevel === 0 ? 15 : (node.localLevel === 1 ? 11 : 6); });
    circles.style('fill', function (node) { return colors(node.group || 'N/A'); });
    if (page.type !== 'PEOPLE') {
      circles.style('stroke', function (node) {
        if (node.localLevel !== 0) return null;
        var color = d3.rgb(colors(node.group || 'N/A'));
        return d3.rgb(Math.round(color.r * 0.85), Math.round(color.g * 0.85), Math.round(color.b * 0.85)).toString();
      }).style('stroke-width', function (node) { return node.localLevel === 0 ? 2 : 0; });
    }
    var labels = people.append('text').attr('class', 'node-text').text(function (node) { return node.name || ''; });
    labels.style('font-size', function (node) { return node.localLevel === 0 ? '12px' : '8px'; })
      .style('font-weight', function (node) { return node.localLevel === 0 ? 'bold' : 'normal'; });
    people.selectAll('text').classed('hidden', !document.getElementById('showLabels').checked);

    people.on('mouseover', function (node) {
      if (personNetwork) {
        if (document.getElementById('showDetails').checked) {
          var matrix = this.getScreenCTM().translate(+this.getAttribute('cx'), +this.getAttribute('cy'));
          tooltip.style.left = (window.pageXOffset + matrix.e + 15) + 'px';
          tooltip.style.top = (window.pageYOffset + matrix.f - 30) + 'px';
          document.getElementById('title').textContent = node.name || '';
          document.getElementById('subtitle').textContent = node.group || '';
          var instruction = document.getElementById('subtitle2');
          instruction.classList.toggle('hidden', node.localLevel === 0);
          instruction.textContent = 'Click to view ' + node.name + "'s " + page.kind;
          tooltip.classList.remove('hidden');
        } else {
          d3.select(this).select('text').style('font-weight', 'bold').style('font-size', '12px');
        }
        var circle = d3.select(this).select('circle');
        if (page.kind === 'coauthors') circle.style('stroke', '#ffbb78').style('stroke-width', 3);
        else circle.style('fill', '#ffbb78');
        return;
      }
      if (!document.getElementById('showDetails').checked) return;
      tooltip.textContent = (node.name || '') + (node.group ? ' — ' + node.group : '');
      tooltip.style.left = (d3.event.clientX + 16) + 'px';
      tooltip.style.top = (d3.event.clientY - 20) + 'px';
      tooltip.classList.remove('hidden');
    }).on('mouseout', function (node) {
      tooltip.classList.add('hidden');
      if (personNetwork) {
        if (!document.getElementById('showDetails').checked) {
          d3.select(this).select('text').style('font-weight', 'normal').style('font-size', '10px');
        }
        var circle = d3.select(this).select('circle');
        if (page.kind === 'coauthors') circle.style('stroke', colors(node.group || 'N/A')).style('stroke-width', 3);
        else circle.style('fill', colors(node.group || 'N/A'));
      }
    });
    people.on('click', function (node) {
      if (page.type === 'PEOPLE' && rootIds.has(node.id)) return;
      var shortId = node.id.split('/').pop();
      if (!/^[A-Za-z0-9_-]{1,80}$/.test(shortId)) return;
      if (page.type === 'PEOPLE') {
        var destination = new URL(window.location.href);
        destination.pathname = destination.pathname.replace('/display/' + page.id + '/viz/', '/display/' + shortId + '/viz/');
        window.location.assign(destination.toString());
      } else window.location.assign('/display/' + shortId + '/');
    });

    var linkForce = d3.forceLink(links).id(function (node) { return node.id; });
    if (!personNetwork || !document.getElementById('forceToFit').checked) {
      linkForce.distance(document.getElementById('forceToFit').checked ? 45 : 100).strength(0.1);
    }
    simulation = d3.forceSimulation(nodes);
    if (!personNetwork) simulation.force('link', linkForce);
    simulation.force('charge', d3.forceManyBody()).force('center', d3.forceCenter(480, 350));
    if (personNetwork) simulation.force('link', linkForce);
    people.call(d3.drag()
      .on('start', function (node) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        node.fx = node.x;
        node.fy = node.y;
      })
      .on('drag', function (node) { node.fx = d3.event.x; node.fy = d3.event.y; })
      .on('end', function () {
        if (personNetwork) document.getElementById('forceToFit').checked = false;
        else simulation.alphaTarget(0);
      }));
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
    if (page.type === 'PEOPLE') {
      url.hash = '';
      url.search = '';
    }
    if (this.checked) url.searchParams.set('fit', '1');
    else url.searchParams.delete('fit');
    window.location.assign(url.toString());
  });

  function svgCode() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="700">\r\n' +
      document.getElementById('svgElement').innerHTML + '\r\n</svg>';
  }
  document.getElementById('embedHtml').addEventListener('click', function () {
    document.getElementById('embedHtmlText').value = '<svg width="960" height="700">\r\n' +
      document.getElementById('svgElement').innerHTML + '\r\n</svg>';
    document.getElementById('embedHtmlDiv').classList.remove('hidden');
    $('html, body').animate({scrollTop: $(document).height() - $(window).height()}, 1400, 'swing');
  });
  document.getElementById('downloadPng').addEventListener('click', function () {
    var status = document.getElementById('downloadStatus');
    status.textContent = 'Preparing image…';
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
        download.download = (page.kind === 'collaborators' ? 'collabs' : page.kind) + '_' + page.id + '.png';
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
