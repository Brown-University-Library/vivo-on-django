(function () {
  'use strict';

  var dataElement = document.getElementById('publication-chart-data');
  if (!dataElement || !window.d3) return;
  var data = JSON.parse(dataElement.textContent);
  var identifier = JSON.parse(document.getElementById('publication-chart-id').textContent);
  var profileAddress = new URL(document.getElementById('organizationProfile').href);
  var profileRoot = profileAddress.pathname.slice(0, profileAddress.pathname.indexOf('/display/')) + '/display/';
  var svg = d3.select('#svgElement');
  var tooltip = document.getElementById('tooltip');
  var colors = d3.scaleOrdinal(d3.schemeCategory20);
  var people = new Map(data.nodes.map(function (person) { return [person.faculty_id, person]; }));
  var level = 1;
  if (!data.matrix.length) document.getElementById('errorMsg').classList.remove('hidden');

  var legend = document.getElementById('legendList');
  data.columns.forEach(function (id) {
    var person = people.get(id);
    if (!person) return;
    var row = document.createElement('li');
    var swatch = document.createElement('span');
    swatch.style.backgroundColor = colors(id);
    swatch.textContent = '\u00a0\u00a0\u00a0\u00a0';
    row.appendChild(swatch);
    row.appendChild(document.createTextNode('\u00a0' + person.name));
    legend.appendChild(row);
  });

  function draw() {
    svg.selectAll('*').remove();
    document.getElementById('showLevel1').classList.toggle('btn-info', level === 1);
    document.getElementById('showLevel1').classList.toggle('btn-default', level !== 1);
    document.getElementById('showLevel2').classList.toggle('btn-info', level === 2);
    document.getElementById('showLevel2').classList.toggle('btn-default', level !== 2);
    var rows = level === 1 ? data.matrix.slice(-10) : data.matrix;
    if (!rows.length) return;
    var margin = {top: 20, right: 20, bottom: 30, left: 50};
    var width = 960 - margin.left - margin.right;
    var height = 700 - margin.top - margin.bottom;
    var plot = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
    var x = d3.scaleBand().domain(rows.map(function (row) { return String(row.year); }))
      .rangeRound([0, width]).paddingInner(0.05).align(0.1);
    var y = d3.scaleLinear().domain([0, d3.max(rows, function (row) { return row.total; }) || 1])
      .nice().rangeRound([height, 0]);
    plot.append('g').selectAll('g').data(d3.stack().keys(data.columns)(rows)).enter()
      .append('g')
      .attr('fill', function (series) { return colors(series.key); })
      .on('mouseover', function (series) {
        d3.select(this).attr('stroke', 'blue').attr('stroke-width', 2);
        if (!document.getElementById('showDetails').checked) return;
        var person = people.get(series.key);
        if (!person) return;
        document.getElementById('title').textContent = person.name;
        document.getElementById('subtitle').textContent = person.group;
        document.getElementById('subtitle2').textContent = 'Click to view publications for this researcher';
        tooltip.style.left = d3.event.pageX + 'px';
        tooltip.style.top = (d3.event.pageY - 28) + 'px';
        tooltip.classList.remove('hidden');
      })
      .on('mouseout', function () {
        d3.select(this).attr('stroke', '').attr('stroke-width', 0);
        tooltip.classList.add('hidden');
      })
      .on('click', function (series) {
        if (/^[A-Za-z0-9_-]{1,80}$/.test(series.key)) {
          window.location.assign(profileRoot + series.key + '#Publications');
        }
      })
      .selectAll('rect').data(function (series) { return series; }).enter().append('rect')
      .attr('x', function (entry) { return x(String(entry.data.year)); })
      .attr('y', function (entry) { return y(entry[1]); })
      .attr('height', function (entry) { return y(entry[0]) - y(entry[1]); })
      .attr('width', x.bandwidth());
    plot.append('g').attr('class', 'axis').attr('transform', 'translate(0,' + height + ')')
      .call(d3.axisBottom(x));
    plot.append('g').attr('class', 'axis').call(d3.axisLeft(y).ticks(null, 's'))
      .append('text').attr('x', 2).attr('y', y(y.ticks().pop()) + 0.5)
      .attr('dy', '0.32em').attr('fill', '#000').attr('font-weight', 'bold')
      .attr('text-anchor', 'start').text('Publications');
  }
  document.getElementById('showLevel1').addEventListener('click', function () { level = 1; draw(); });
  document.getElementById('showLevel2').addEventListener('click', function () { level = 2; draw(); });

  function svgCode() {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="700">\r\n' +
      '<rect width="100%" height="100%" fill="white"/>\r\n' +
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
        var url = URL.createObjectURL(blob);
        var download = document.createElement('a');
        download.href = url;
        download.download = 'collabs_' + identifier + '.png';
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
  draw();
}());
