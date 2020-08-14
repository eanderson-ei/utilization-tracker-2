var d1 = new Date(2020, 03, 29, 0, 0, 0, 0);
var d2 = new Date(2021, 03, 31, 0, 0, 0, 0);

var update = {
	title: 'New Title',
	'xaxis.range': [d1,d2],
  yaxis: {
    showgrid: true,
    zeroline: true,
    showline: true,
    mirror: 'ticks',
    gridcolor: '#bdbdbd',
    gridwidth: 2,
    zerolinecolor: '#969696',
    zerolinewidth: 4,
  }
}

Plotly.relayout(utilization-chart, update);
utilization-chart._fullLayout.xaxis._rangeInitial = [d1, d2]