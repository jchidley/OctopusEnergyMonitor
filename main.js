function plotme(loc, data) {
    // The data has been sent as a plotly chart encoded as JSON, including the 
    // 'layout' and 'config' information. To change 'layout' and 'config' you 
    // need to send 'data', 'layout' and 'config' seperately to the display function.
    // Things can be adjusted individually as below.
    // graph['layout']['showlegend'] = false; // change options
    graph = JSON.parse(data);
    Plotly.react(document.getElementById(loc), graph['data'], graph['layout'], { responsive: true });
}


function replaceMe(loc, data) {
    document.getElementById(loc).innerHTML = data;
}


function loadingData() {
    fetch('http://localhost:8000')
        .then(function (response) { return response.json() })
        .then(function (data) {
            replaceMe("missing_gas", data.missing_gas);
            replaceMe("missing_electric", data.missing_electric);
            replaceMe("recent_gas", data.recent_gas);
            replaceMe("recent_electric", data.recent_electric);
        });
}


function starttimes() {
    fetch('http://localhost:8000/starttimes')
        .then(function (response) { return response.json() })
        .then(function (data) {
            replaceMe("WashingMachineEnd", data.WashingMachineEnd);
            replaceMe("WashingMachineCost", data.WashingMachineCost);
            replaceMe("GentleDishwasherStart", data.GentleDishwasherStart);
            replaceMe("GentleDishwasherCost", data.GentleDishwasherCost);
            replaceMe("EcoDishwasherStart", data.EcoDishwasherStart);
            replaceMe("EcoDishwasherCost", data.EcoDishwasherCost);
            replaceMe("IntenseDishwasherStart", data.IntenseDishwasherStart);
            replaceMe("IntenseDishwasherCost", data.IntenseDishwasherCost);
            plotme('WashingMachinePlot', data.WashingMachinePlot);
            plotme('GentleDishwasherPlot', data.GentleDishwasherPlot);
            plotme('EcoDishwasherPlot', data.EcoDishwasherPlot);
            plotme('IntenseDishwasherPlot', data.IntenseDishwasherPlot);
        });
}


function consumption() {
    fetch('http://localhost:8000/consumption')
        .then(function (response) { return response.json() })
        .then(function (data) {
            plotme("electricityDailyChart", data.electricityDailyChart);
            plotme("electricityRollingChart", data.electricityRollingChart);
            plotme("gasDailyChart", data.gasDailyChart);
            plotme("gasRollingChart", data.gasRollingChart);
            plotme("gasConsumptionBinnedChart", data.gasConsumptionBinnedChart);
            plotme("gasConsumption2022BinnedChart", data.gasConsumption2022BinnedChart);
        });
}