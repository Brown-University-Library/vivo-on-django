(function () {
  'use strict';

  var dataElement = document.getElementById('publication-chart-data');
  if (!dataElement || !window.d3) return;
  var data = JSON.parse(dataElement.textContent);
  var identifier = JSON.parse(document.getElementById('publication-chart-id').textContent);
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
    row.appendChild(swatch);
    row.appendChild(document.createTextNode(person.name));
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
    plot.selectAll('.publication-series').data(d3.stack().keys(data.columns)(rows)).enter()
      .append('g').attr('class', 'publication-series')
      .attr('fill', function (series) { return colors(series.key); })
      .style('cursor', 'pointer')
      .on('mouseover', function (series) {
        d3.select(this).attr('stroke', 'blue').attr('stroke-width', 2);
        if (!document.getElementById('showDetails').checked) return;
        var person = people.get(series.key);
        if (!person) return;
        tooltip.textContent = person.name + (person.group ? ' — ' + person.group : '');
        tooltip.style.left = (d3.event.clientX + 12) + 'px';
        tooltip.style.top = (d3.event.clientY - 24) + 'px';
        tooltip.classList.remove('hidden');
      })
      .on('mouseout', function () {
        d3.select(this).attr('stroke', null).attr('stroke-width', null);
        tooltip.classList.add('hidden');
      })
      .on('click', function (series) {
        if (/^[A-Za-z0-9_-]{1,80}$/.test(series.key)) {
          window.location.assign('/display/' + series.key + '#Publications');
        }
      })
      .selectAll('rect').data(function (series) { return series; }).enter().append('rect')
      .attr('x', function (entry) { return x(String(entry.data.year)); })
      .attr('y', function (entry) { return y(entry[1]); })
      .attr('height', function (entry) { return y(entry[0]) - y(entry[1]); })
      .attr('width', x.bandwidth());
    plot.append('g').attr('class', 'axis').attr('transform', 'translate(0,' + height + ')')
      .call(d3.axisBottom(x));
    plot.append('g').attr('class', 'axis').call(d3.axisLeft(y).ticks(null, 's'));
    plot.append('text').attr('x', 2).attr('y', 4).attr('font-weight', 'bold')
      .attr('font-size', 10).text('Publications');
  }
  document.getElementById('showLevel1').addEventListener('click', function () { level = 1; draw(); });
  document.getElementById('showLevel2').addEventListener('click', function () { level = 2; draw(); });

  function svgCode() {
    var image = document.getElementById('svgElement').cloneNode(true);
    image.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
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
        download.download = 'publications_' + identifier + '.png';
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
