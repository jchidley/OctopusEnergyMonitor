/* jshint bitwise: true */
/* jshint curly: true */
/* jshint eqeqeq: true */
/* jshint esversion: 11 */
/* jshint forin: true */
/* jshint freeze: true */
/* jshint futurehostile: true */
/* jshint globals: true */
/* jshint latedef: true */
/* jshint leanswitch: true */
/* maxcomplexity: true */ // read up
/* jshint maxdepth: 3 */
/* maxerr: true */ // remove
/* jshint maxparams: 3 */
/* jshint maxstatements: 4 */
/* jshint nocomma: true */
/* jshint nonbsp: true */
/* jshint nonew: true */
/* jshint noreturnawait: true */
/* jshint predef: true */
/* jshint regexpu: true */
/* jshint shadow: true */
/* jshint singleGroups: true */
/* jshint strict: true */
/* jshint trailingcomma: true */
/* jshint undef: true */
/* jshint unused: true */
/* jshint varstmt: true */

/* globals Plotly, document */

/*
https://jshint.com/docs/options
let t = document.querySelector("table"); // first table, should be the enforcing one
let ids = Array.from(t.querySelectorAll("tr>td[id]")); // the ids
let filtered = ids.filter(i => !i.parentElement.innerHTML.includes('deprecated'));
let strictOptions = filtered.map(i => {return i.id + ": true"}).join(", ");
strictOptions = filtered.map(i => {return '/* jshint ' + i.id + ": true 
* /"}).join("\n") // remove space to get comment to work
*/

function plotme(loc, data) {
    "use strict";
    // The data has been sent as a plotly chart encoded as JSON, including the
    // 'layout' and 'config' information. To change 'layout' and 'config' you
    // need to send 'data', 'layout' and 'config' seperately to the display
    // function. Things can be adjusted individually as below.
    // graph['layout']['showlegend'] = false; // change options
    let graph = JSON.parse(data);
    let config = { responsive: true };
    Plotly.react(
        document.getElementById(loc),
        graph.data,
        graph.layout,
        config
    );
}

function replaceMe(loc, data) {
    "use strict";
    document.getElementById(loc).innerHTML = data;
}

function loadingData() {
    "use strict";
    fetch("http://localhost:8000/startpage")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            replaceMe("missing_gas", data.missing_gas);
            replaceMe("missing_electric", data.missing_electric);
            replaceMe("recent_gas", data.recent_gas);
            replaceMe("recent_electric", data.recent_electric);
        });
}

function starttimes() {
    "use strict";
    fetch("http://localhost:8000/starttimes")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            replaceMe("WashingMachineEnd", data.WashingMachineEnd);
            replaceMe("WashingMachineCost", data.WashingMachineCost);
            replaceMe("GentleDishwasherStart", data.GentleDishwasherStart);
            replaceMe("GentleDishwasherCost", data.GentleDishwasherCost);
            replaceMe("EcoDishwasherStart", data.EcoDishwasherStart);
            replaceMe("EcoDishwasherCost", data.EcoDishwasherCost);
            replaceMe("IntenseDishwasherStart", data.IntenseDishwasherStart);
            replaceMe("IntenseDishwasherCost", data.IntenseDishwasherCost);
            plotme("WashingMachinePlot", data.WashingMachinePlot);
            plotme("GentleDishwasherPlot", data.GentleDishwasherPlot);
            plotme("EcoDishwasherPlot", data.EcoDishwasherPlot);
            plotme("IntenseDishwasherPlot", data.IntenseDishwasherPlot);
        });
}

function consumption() {
    "use strict";
    fetch("http://localhost:8000/consumption")
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            plotme("electricityDailyChart", data.electricityDailyChart);
            plotme("electricityRollingChart", data.electricityRollingChart);
            plotme("gasDailyChart", data.gasDailyChart);
            plotme("gasRollingChart", data.gasRollingChart);
            plotme("gasConsumptionBinnedChart", data.gasConsumptionBinnedChart);
            plotme(
                "gasConsumption2022BinnedChart",
                data.gasConsumption2022BinnedChart
            );
            plotme(
                "gasConsumption2023BinnedChart",
                data.gasConsumption2023BinnedChart
            );
            plotme(
                "gasConsumption2024BinnedChart",
                data.gasConsumption2024BinnedChart
            );
        });
}
