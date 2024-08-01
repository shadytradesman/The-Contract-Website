var viewWidth = $("#visContainer").width();

var margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = viewWidth - margin.left - margin.right,
        height = ($( window ).height() * .5);

var color = d3.scale.ordinal()
        .range(["#d5d5d5","#92c5de","#0571b0","#ca0020","#f4a582"]);

var svg = d3.select('#visContainer').append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x0 = d3.scale.ordinal()
        .rangeRoundBands([0, width], .1);

var x1 = d3.scale.ordinal();

var xAxis = d3.svg.axis()
        .scale(x0)
        .tickSize(0)
        .orient("bottom");

function renderRollName(rollType) {
    var start = rollType.dice + " d10 at Difficulty " + rollType.difficulty;
    if (rollType.type === 'standard') {
        return start;
    }
    else if(rollType.type === "botchesAndDoubles") {
        return start + " with botches and doubles";
    } else {
        return start + " with " + rollType.type;
    }
};

function updateVis() {
    var rollTypes = []
    $(".js-roll").each(function(index) {
        var rolldiv = $( this );
        var num_dice = rolldiv.find(".num-dice").val();
        var difficulty = rolldiv.find(".difficulty").val();
        var is_include_botches = rolldiv.find(".botches")[0].checked;
        var is_include_doubles = rolldiv.find(".doubles")[0].checked;
        var type = "standard";
        if (is_include_botches && is_include_doubles) {
            type = "botchesAndDoubles";
        } else if (is_include_doubles) {
            type = "doubles";
        } else if (is_include_botches) {
            type = "botches";
        }
        var rollType = {
            type: type,
            dice: num_dice,
            difficulty: difficulty
        };
        rollTypes.push(rollType);
    });

    var useExactOutcomeOdds = $('input[name=exactOutcome]:checked').val() == 1;

    d3.json(dataUrl, function(error, data) {
        d3.selectAll("svg .legend").remove();
        d3.selectAll("svg .dom").remove();
        d3.selectAll("svg .x").remove();
        d3.selectAll("svg .y").remove();

        var outcomeNames = new Set();
        var rollNames = [];
        rollTypes.forEach(function(type) {
            Object.keys(data[type.type][type.dice][type.difficulty]).forEach(function(outcome) {
                outcomeNames.add(parseInt(outcome,10));
            });
            rollNames.push(renderRollName(type));
        });
        outcomeNames = [...outcomeNames];
        outcomeNames.sort(function(a,b){return a - b});
        var oddsByTypeByOutcome = {};
        var maxOdds = 0;
        outcomeNames.forEach(function(outcome) {
            oddsByTypeByOutcome[outcome] = [];
            var newList = [];
            rollTypes.forEach(function(type) {
                var odds;
                if (useExactOutcomeOdds) {
                    odds = data[type.type][type.dice][type.difficulty][outcome];
                    odds = odds ? Number(odds) : 0;
                    odds = odds * 100;
                } else {
                    var outcomes = Object.keys(data[type.type][type.dice][type.difficulty]);
                    var totalOdds = 100;
                    outcomes.forEach(function(out) {
                        var odds = data[type.type][type.dice][type.difficulty][out];
                        odds = odds ? Number(odds) * 100 : 0;
                        if (out < outcome) {
                            totalOdds =  totalOdds - odds;
                        }
                    });
                    if (totalOdds >= 100) {
                        totalOdds = 100;
                    }
                    odds = totalOdds >= 0 ? totalOdds : 0;
                }
                if (odds > maxOdds) {
                    maxOdds = odds;
                }
                newList.push({
                    type: renderRollName(type),
                    odds: odds
                });
                oddsByTypeByOutcome[outcome][odds] = odds;
            });
            oddsByTypeByOutcome[outcome] = newList;
        });

        x0.domain(outcomeNames);
        x1.domain(rollNames).rangeRoundBands([0, x0.rangeBand()]);

        var y = d3.scale.linear()
                .domain([0, maxOdds])
                .range([height, 0]);

        var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left");

        svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .style('font-weight','bold');
        svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + height + ")")
                .call(xAxis);

        var slice = svg.selectAll(".slice")
                .data(Object.keys(oddsByTypeByOutcome))
                .enter().append("g")
                .attr("class", "g dom")
                .attr("transform", function(d) { return "translate(" + x0(d) + ",0)"; });
        slice.selectAll(".bar")
            .data(function(outcome) {var out = oddsByTypeByOutcome[outcome]; return out;})
            .enter().append("rect")
                .attr("width", x1.rangeBand())
                .attr("x", function(d) { return x1(d["type"]); })
                .style("fill", function(d, i) { return color(i) })
                .attr("y", function(d) { return y(0); })
                .attr("height", function(d) { return height - y(0); })
                .attr("class", "bar");

        slice.selectAll(".mouseover")
            .data(function(outcome) {var out = oddsByTypeByOutcome[outcome]; return out;})
            .enter().append("rect")
                .attr("width", x1.rangeBand())
                .attr("x", function(d) { return x1(d["type"]); })
                .style("fill", function(d) { return "rgba(255,255,255,0)" })
                .attr("y", function(d) { return y(maxOdds); })
                .attr("height", function(d) { return y(0); })
                .attr("class", "mouseover")
                .attr("data-toggle", "tooltip")
                .attr("data-container", "body")
                .attr("data-viewport", '{ "selector": "#odds-display"}')
                .attr("title", function(d) {return d["odds"] + "%";})
                .attr("data-placement", "right")
                .on("mouseover", function(d) {
                        d3.select(this).style("fill", "rgba(255,255,255,.1)");
                })
                .on("mouseout", function(d) {
                        d3.select(this).style("fill", "rgba(255,255,255,0)");
                });

        slice.selectAll(".bar")
                .transition()
                .delay(function (d) {return Math.random()*300;})
                .duration(400)
                .attr("y", function(d) { return y(d["odds"]); })
                .attr("height", function(d) {
                    return height - y(d["odds"]);
                });


        //Legend
        var legend = svg.selectAll(".legend")
                .data(rollTypes.map(function(type) {return renderRollName(type);}))
        .enter().append("g")
                .attr("class", "legend")
                .attr("transform", function(d,i) { return "translate(0," + i * 20 + ")"; })
                .style("opacity","0");

        legend.append("rect")
                .attr("x", width - 18)
                .attr("width", 18)
                .attr("height", 18)
                .style("fill", function(d, i) { return color(i); });

        legend.append("text")
                .attr("x", width - 24)
                .attr("y", 9)
                .attr("dy", ".35em")
                .style("text-anchor", "end")
                .text(function(d) {return d; });

        legend.transition().duration(500).delay(function(d,i){ return 300 + 100 * i; }).style("opacity","1");
        $('[data-toggle="tooltip"]').tooltip();
    });
    $('[data-toggle="tooltip"]').tooltip();
}

$(function () {
  updateVis();
})

$("select").on("change", function() {
    updateVis();
});

$(".checkboxes").on("click", function() {
    updateVis();
});

$(".radio-inline").on("change", function() {
    updateVis();
});