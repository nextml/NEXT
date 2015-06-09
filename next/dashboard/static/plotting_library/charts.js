/*charts2.js - A javascript plotting library.

  Last Date Modified: May 4, 2015
  Authors: Lalit Jain, Nick Glattard
*/

var colorsChart = [["#31a354"],["#3182bd"],["#756bb1"],["#636363"],["#c70076"],["#45bdbd"],["#"],["#"]];
var buttonsChart = [["#A9A9C6"]];

var charts = (function(data) {

    /**
     * Takes in the raw data set and converts it into a list of dictionaries required for plotting a stacked area plot
     * @param list - the raw data set
     * @param name - (optional) used to filter particular data from the the raw data set
     * @returns {{data: Array of values we have to plot,
      * numberOfPlots: number of plots that stack on,
      * namesOfYAxes: labels for legend,
      * yAxisLabel: y axis label
      * }}
     */

    var font_size = 16;
    var legend_font_size = 13;

    data.format_data_for_stacked_area_chart = function(list,name){

        var numberOfPlots=0;  // holds the number of line charts
        var namesOfYAxes =[]; // array that stores names of legends

        var raw_data = list.data; // the data values we need to plot
        var data_object; // temporay variable to hold each row of raw data object

        var crossfilter_data=[]; // final array we return
        var number_of_data_points =0; // number of x axis points
        var maxIndex; // the row of raw data with maximum number of x values

        // this part becomes relevant only when the legends are interactive
        // it goes through the list and returns only the data values for the legend we
        // clicked on
        if(typeof name == 'string'){

            // building array with names of legends
            for (var key in raw_data) {
                data_object = raw_data[key];

                if(data_object.y.length > number_of_data_points){
                    number_of_data_points = data_object.y.length;
                    maxIndex = numberOfPlots;
                }
                namesOfYAxes[numberOfPlots] = data_object.legend_label;
                numberOfPlots ++ ;
            }

            // getting row of the legend we are interested in plotting (for interactive legends only)
            var j =$.inArray(name, namesOfYAxes);

            /*
             Converting to correct format of data for plotting
             */
            //number_of_data_points = data_object.t.length;
            for (var i = 0; i < number_of_data_points; i++) {
                crossfilter_data[i] = {};

                if(typeof raw_data[j].y[i] == 'number'){
                    //eval("crossfilter_data[i]."+name+" = (raw_data["+j+"].y[i]);");
                    crossfilter_data[i][name] = raw_data[j].y[i];

                }
                else{
                    //eval("crossfilter_data[i]."+name+" = 0;");
                    crossfilter_data[i][name] = 0;
                }
                crossfilter_data[i].x = list.x[i];
                crossfilter_data[i].t = list.t[i];

                // purposely put here so we can make the legends go back to original state
                //crossfilter_data[i].all = 0;

            }

            return {'data':crossfilter_data,'numberOfPlots':numberOfPlots,'namesOfYAxes': namesOfYAxes,
                'yAxisLabel' :list.y_label};

        }
        else{
            var max_log_y =-10000;
            var min_log_y = 10000;

            // building array with names of legends
            for (var key in raw_data) {
                data_object = raw_data[key];

                if(data_object.y.length > number_of_data_points){
                    number_of_data_points = data_object.y.length;
                    maxIndex = numberOfPlots;
                }
                namesOfYAxes[numberOfPlots] = data_object.legend_label;
                numberOfPlots ++ ;
            }

            /*
             Converting to correct format of data for plotting
             */
            var j=0;
            for (var i = 0; i < number_of_data_points; i++) {
                crossfilter_data[i] = {};
                while(j< numberOfPlots){
                    //crossfilter_data[i].RandomSampling0time = raw_data[0].t[i];
                    if(typeof raw_data[j].y[i] == 'number'){
                        //eval("crossfilter_data[i]."+namesOfYAxes[j]+" = (raw_data["+j+"].y[i]);");
                        crossfilter_data[i][namesOfYAxes[j]] = (raw_data[+j].y[i]);

                        if(raw_data[j].y[i] !=0){
                            if(max_log_y < Math.log10(raw_data[j].y[i])){
                                max_log_y = Math.log10(raw_data[j].y[i]);
                            }

                            if(min_log_y > Math.log10(raw_data[j].y[i])){
                                min_log_y = Math.log10(raw_data[j].y[i]);
                            }
                        }
                    }
                    else{
                        //eval("crossfilter_data[i]."+namesOfYAxes[j]+" = 0;");
                        crossfilter_data[i][namesOfYAxes[j]] = 0;
                    }
                    j++;
                }
                crossfilter_data[i].x = list.x[i];
                crossfilter_data[i].t = list.t[i];

                // purposely put here so we can make the legends go back to original state
                //crossfilter_data[i].all = 0;

                j=0;
            };

            return {'data':crossfilter_data,'numberOfPlots':numberOfPlots,'namesOfYAxes': namesOfYAxes,
                'yAxisLabel' :list.y_label, 'min_log_y':min_log_y, 'max_log_y': max_log_y};
        }
    }


    /**
     *
     * Takes in the raw data set and converts it into a list of dictionaries required for plotting a multi line plot
     * @param list - the raw data set
     * @param name - (optional) used to filter particular data from the the raw data set
     * @returns {{
     * data: Array of values we have to plot,
     * numberOfPlots: number of plots that stack on,
     * namesOfYAxes: labels for legend,
     * labels: legend labels,
     * x_max: maximum value for x array
     * }}
     */
    data.format_data_for_multi_line_chart = function (list,name){

        var numberOfPlots=0; // holds the number of line charts
        var namesOfYAxes =[];// array that stores names of legends
        var labels =[];

        var raw_data = list.data; // the data values we need to plot
        var data_object; // temporay variable to hold each row of raw data object
        var crossfilter_data=[]; // final data array we return
        var number_of_data_points =0; // number of x axis points
        var maxIndex; // the row of raw data with maximum number of x values

        var x_max; // maximum value for x

        // making legend label array
        for (var key in raw_data) {
            data_object = raw_data[key];

            if(data_object.t.length > number_of_data_points){
                number_of_data_points = data_object.t.length;
                maxIndex = numberOfPlots;
            }
            labels[numberOfPlots] = data_object.legend_label;
            numberOfPlots ++ ;
        }

        // this part becomes relevant only when the legends are interactive
        // it goes through the list and returns only the data values for the legend we
        // clicked on
        if(typeof name == 'string'){


            /*
             Converting to correct format of data for plotting
             */

            //getting ride of spacing in keys
            for(var i=0; i< labels.length; i++){
                namesOfYAxes[i] = labels[i].split(" ")[0];
            }

            // getting row of the legend we are interested in plotting (for interactive legends only)
            var j =$.inArray(name, namesOfYAxes);
            for (var i = 0; i < number_of_data_points; i++) {
                crossfilter_data[i] = {};

                if(typeof raw_data[j].y[i] == 'number'){
                    //eval("crossfilter_data[i]."+name+"time = raw_data["+j+"].t[i];");
                    //eval("crossfilter_data[i]."+name+" = (raw_data["+j+"].y[i]);");
                    crossfilter_data[i][name+"time"] = raw_data[j].t[i];
                    crossfilter_data[i][name] = raw_data[j].y[i];
                }
                else{
//                    crossfilter_data[i][name+"time"] = 0;
//                    crossfilter_data[i][name] = 0;
                }

                crossfilter_data[i].x = raw_data[maxIndex].x[i];

                // done to re filter original data; dummy value given
                //crossfilter_data[i].all = -5;

            };
            x_max = list.x_max;
            return {'data':crossfilter_data,'numberOfPlots':numberOfPlots,'namesOfYAxes': namesOfYAxes,'labels':labels,
                'x_max':x_max};

        }
        else{

            var max_log_y =-10000;
            var min_log_y = 10000;
            /*
             Converting to correct format of data for plotting
             */

            // getting ride of spacing in keys
            for(var i=0; i< labels.length; i++){
                namesOfYAxes[i] = labels[i].split(" ")[0];
            }

            var j=0;
            for (var i = 0; i < number_of_data_points; i++) {
                crossfilter_data[i] = {};
                while(j< numberOfPlots){
                    if(typeof raw_data[j].y[i] == 'number'){
                        crossfilter_data[i][namesOfYAxes[j]+"time"] = raw_data[j].t[i];
                        crossfilter_data[i][namesOfYAxes[j]] = raw_data[j].y[i];

                        if(raw_data[j].y[i] !=0){
                            if(max_log_y < Math.log10(raw_data[j].y[i])){
                                max_log_y = Math.log10(raw_data[j].y[i]);
                            }

                            if(min_log_y > Math.log10(raw_data[j].y[i])){
                                min_log_y = Math.log10(raw_data[j].y[i]);
                            }
                        }
                    }

                    j++;
                }
                crossfilter_data[i].x = raw_data[maxIndex].x[i];

                // done to re filter original data; dummy value given
                //crossfilter_data[i].all = -5;
                j=0;
            };
            // getting max x value
            x_max = list.x_max;
            return {'data':crossfilter_data,'numberOfPlots':numberOfPlots,'namesOfYAxes': namesOfYAxes,'labels':labels,
                'x_max':x_max, 'min_log_y':min_log_y, 'max_log_y': max_log_y};
        }
    }

    /**
     *
     * @param data_in - the raw data object we want plotted
     * @param div - the name of the div element that we want to attach plot to
     * @param label - plot title
     */
    data.make_histogram = function(data_in,div,label, height, width){

        // format of time stamp in data
        var format = d3.time.format("%Y-%m-%d %X %L");

        // A formatter for counts.
        var formatCount = d3.format(",.0f");

        /**
         *  function to get date in the right format
         * @param timeData - array of time stamps
         * @returns {formatted time stamp based on formate declared above}
         */
        var getDateFormat = function(timeData){

            // temporary variable to hold all parts of the time stamp
            var testing_time = timeData.split(" ");

            // temporary variable to hold millisecond part of the time stamp
            var millisecond_split = testing_time[1].split(".");
            //millisecond_split[1]= millisecond_split[1].substring(0,3);

            // array with the year, month and date
            var year_month_day = testing_time[0].split("-");
            // array with hours, minutes and seconds
            var hours_minutes_seconds= millisecond_split[0].split(":");

            var test_date =format(
                new Date(year_month_day[0],year_month_day[1],year_month_day[2],
                    hours_minutes_seconds[0],hours_minutes_seconds[1],hours_minutes_seconds[2],
                    millisecond_split[1]
                ));

            if(hours_minutes_seconds.length !=3){
                //hours_minutes_seconds[hours_minutes_seconds.length] = String(0);
                return -1;
            }
            if(millisecond_split.length !=2){
                //millisecond_split[millisecond_split.length] = String(0);
                return -1;
            }
            return test_date;

        }

        // the data we are plotting
        var data_to_be_plotted = [];

        for(var i = 0, j=0; i< data_in.data.t.length-1; i++){
            if(getDateFormat(data_in.data.t[i]) != -1){
                data_to_be_plotted[j++] = getDateFormat(data_in.data.t[i]);
            }
        }

        // specify number of bins

        var num_bins = Math.round(Math.log2(data_to_be_plotted.length));
        // console.log("data", data_to_be_plotted)
        // console.log("min", d3.min(data_to_be_plotted, function(d){ return d}))

        // var margin = {top: 50, right: 0.1*width, bottom: 140, left: 0.1*width}; 
        var margin = {top: 0.1*height, right: 0.1*width, bottom: 140, left: 0.1*width};

        // setting up x axis domain and range
        var x = d3.time.scale()
            .domain([format.parse(d3.min(data_to_be_plotted, function(d){ return d})),
                format.parse(d3.max(data_to_be_plotted, function(d){ return d}))])
            .range([0, 0.8*width])
            .nice(.8*width)

        // console.log("ticks",x.ticks(d3.time.second, 5))
        // Generate a histogram using "num_bins" uniformly-spaced bins.
        var data = d3.layout.histogram()
            .bins(num_bins)
            .value(function (d) {
                return format.parse(d).getTime()
            })
            .range([format.parse(d3.min(data_to_be_plotted, function(d){ return d})),
                format.parse(d3.max(data_to_be_plotted, function(d){ return d}))])
        (data_to_be_plotted);

        // setting up y axis domain and range
        var y = d3.scale.linear()
            .domain([0, d3.max(data, function(d) { return d.y; })])
            .range([height, 0 ]); // removed the 0.7*height for chart

        // set up ticks
        // var tick_values = []
        // for(var i = 0; i < data.length; i++){
        //   tick_values[i] = format.parse(data[i].x)
        // }
        // console.log("tick values",tick_values)
        // var x_minn = format.parse(d3.min(data_to_be_plotted, function(d){ return d}))
        // console.log(x_minn)
        // var x_maxx = format.parse(d3.max(data_to_be_plotted, function(d){ return d}))
        // console.log(x_maxx)
        // console.log(num_bins)
        // console.log(d3.range(x_minn, x_maxx, num_bins))

        // physical appearance of x Axis
        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom")
            // .tickValues(tick_values)
            .ticks(num_bins)
            // .ticks(d3.time.second, function(d) { return x(d.x+d.dx)-x(d.x) })
            .tickFormat(d3.time.format("%m-%d-%y %X"));

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");
//            .ticks(10, "%");

        // the svg element we attach bars to
        var svg = d3.select("#"+div).append("svg")
            .attr("id",div+"svg_histogram")
            .attr("width", width)
            .attr("height", 2*height)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
        // responsive SVG
        // .classed("svg-container", true)
        // .attr("preserveAspectRatio", "xMinYMin meet")
        // .attr("viewBox", "0 0 600 400")
        //class to make it responsive
        // .classed("svg-content-responsive", true);


        /* Chart title */
        svg.append("text")
            .attr("class", "title")
            .attr("x", 0.5 *.8*width)
            .attr("y", 0 - (margin.top / 2))
            .attr("text-anchor", "middle")
            .style({"font-size":font_size, "fill":"#7d7d7d" })
            .text(label);

        var bar = svg.selectAll(".bar")
            .data(data)
            .enter().append("g")
            .attr("class", "bar")
            .attr("transform", function(d) { return "translate(" + x(d.x) + "," + (y(d.y)) + ")"; });

        // the bar
        bar.append("rect")
            .data(data)
            .attr("y", function(d) { return 0; })
            .attr("x",0)
            .attr("stroke", "#FFF")
            .attr("fill", colorsChart[2])
            .attr("width", function(d) {return x(d.x+d.dx)-x(d.x);})
            .attr("height", function(d) { return height - y(d.y); });

        // text
        bar.append("text")
            .attr("y", -5)
            .attr("x", function(d) { return (x(d.x+d.dx)-x(d.x))/2 })
            .attr("text-anchor", "middle")
            .attr("fill","black")
            .text(function(d) { return formatCount(d.y); });

        svg.append("g")
            .attr("class", "y axis")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style('shape-rendering', 'crispEdges')
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end");



        // rotating x axis to fit data
        svg.append("g")
            .attr("class", "x axis")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style("font-size","10px")
            .style('shape-rendering', 'crispEdges')
            .attr("transform", "translate("+ 0 +"," + height + ")")
            .call(xAxis)
            .selectAll("text")
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", "-.5em")
            // .attr("transform", "translate("+ 20 +"," + 0 + ")")
            .attr("transform", function(d) {
                return "rotate(-90)" // changed from 89 to 90
            })

        // Add the text label for the x axis : hardcoded position: part of it(the offest only)
        svg.append("text")
            .attr("transform", "translate(" + (width / 2-75) + " ," + (height + margin.bottom-20) + ")")
            .style("text-anchor", "middle")
            .style({"font-size":font_size, "fill":"#7d7d7d" })
            .text(data_in.x_label);

        // Add the text label for the Y axis
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0- 40)
            .attr("x",0 - (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style({"font-size":font_size, "fill":"#7d7d7d" })
            .text(data_in.y_label);

    }

    data.make_multi_line_chart = function(data_in,div,label,height,width){

        var raw_data = data_in;

        var myDataSource = data.format_data_for_multi_line_chart(data_in);

        // an array used to filter non numeric data
        var checker_array =["x"];
        var checker_array_index =checker_array.length;

        for(var i in myDataSource.data[0]){

            if(typeof myDataSource.data[0][i] !='number'){
                checker_array[checker_array_index] =String(i);
                checker_array_index++;
            }
        }

        render_plot(myDataSource,raw_data, false);

        function render_plot(dataSource,raw_data, is_log) {

            var xLabel = raw_data.x_label;
            var yLabel = raw_data.y_label;

            var x_max = dataSource.x_max;
            var x_min = dataSource.x_min;

            var y_max = dataSource.y_max;
            var y_min = dataSource.y_min;

            var margin = {top: 0.1*height, right: 0.1*width, bottom: 30, left: 0.1*width}

            // set up x and y axis
            var x = d3.scale.linear()
                .domain([0, x_max])
                .range([0, 0.8*width]);

            var y;
            if(!is_log){
                y= d3.scale.linear()
                    .range([0.7*height, 0])

            }
            else{
                y= d3.scale.log()
                    .range([0.7*height, 0]).nice();
            }

            // define x axis
            var xAxis = d3.svg.axis()
                .scale(x)
                .tickFormat(d3.format(",.2f"))
                .orient("bottom")
                .tickFormat(function(d){  return d ; })

            var yAxis = d3.svg.axis()
                .scale(y)
                .ticks(20, "e")
//                .tickFormat(d3.format(",.2f"))
                .orient("left");

	    if(is_log){
		yAxis = d3.svg.axis()
		    .scale(y)
		    .ticks(10,"e")
		    .orient("left")
		;
	    }
            /* Lines */

            var line = d3.svg.line()
                .x(function(d) {
                    return x(d.x_val);
                })
                .y(function(d) {
                    if(isNaN(d.y_val) == false)
                        return y(d.y_val);
                });

            var zoom = d3.behavior.zoom()
                .scaleExtent([1, 2])
                .on("zoom", zoomed);

            function zoomed() {
                console.log(" I am zooming")
                svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
            }

            /* Canvas */
            var svg = d3.select("#"+div).append("svg")
                .attr("id",div+"svg_multi_line_plot")
                //.call(zoom)
                .attr("width", width) // + margin.left + margin.right)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");




            /* Chart title */
            svg.append("text")
                .attr("class", "title")
                .attr("x", 174).attr("y", -25).attr("text-anchor", "middle")
                .style({"font-size":font_size, "fill":"#7d7d7d" })
                .text(label);



            /* Draw chart */
            var drawData = function(dataSource, raw_data, xAxisLabel, yAxisLabel){
                // the data that comes in is the formated data i've been printing

                data_in = dataSource.data;
                var colorArray = d3.scale.ordinal().range(colorsChart);

                // buttons for linear and log option
                var linlog  = d3.scale.ordinal().domain(["linear","log"]);
                linlog.range(buttonsChart);

                /* Mapping data (use checker array to filter out the non numeric stuff)*/
                colorArray.domain(d3.keys(data_in[0]).filter(function(key) {
                    var check =  $.inArray(key, checker_array) < 0;
                    return check == true;
                }));



                var dictionary_for_plotting = colorArray.domain().map(function(name) {
                    return {
                        name: name, // name of year or in our case the y label
                        values: data_in.map(function(d) { // the month value(x in our case) and the correct y value
                            var timeName = name+"time";
                            var dateValue = d[timeName];
                            var y_val = d[name];
                            if(y_val !== "") { y_val = +d[name] }

                            //CONFUSION: ASK LALIT WHICH ONE IS RIGHT
                            if(is_log){

//                                y_val = (Math.log10(y_val));
                                y_val = y_val;
                            }

                            // returning x value and the data value i want
                            return {x_val: d.x, y_val: y_val ,date : dateValue};
                        })
                    };
                });


                /* Remove some rows that percentage is null */
                for(var i in dictionary_for_plotting){
                    var values = dictionary_for_plotting[i].values;
                    for(var j = values.length-1 ; j>=0 ; j--){
                        if(values[j].percentage === ""){
                            values.splice(j,1);
                        }
                    }
                }

                /* Getting max and min of all y values; may not even need */
                y_min =0;
                y_max = raw_data.y_max + raw_data.y_max/2;

                if(!is_log){
                    y.domain([ y_min, y_max ]);

//                    Testing purposes only:
//                    y.domain([ 0.1, 10000 ]);

                }
                else{
//                    y.domain([dataSource.min_log_y, dataSource.max_log_y]);
                      y.domain([ 0.000001, y_max ]);

//                    Testing purposes only:
//                    y.domain([ 0.1, 10000 ]);

                }
                console.log(y.domain());
                console.log(dictionary_for_plotting);
                svg.append("g")
                    .attr("class", "y axis yAxis")
                    .style('fill', 'none')
                    .style('stroke', '#000')
                    .style('shape-rendering',"crispEdges")
                    .call(yAxis)
                    .append("text")
                    .attr("transform", "rotate(-90)")
                    .style("stroke","#000");


                // Add the text label for the Y axis
                svg.append("text")
                    .attr("transform", "rotate(-90)")
                    .attr("y", 0- 35)
                    .attr("x",0 - (0.7*height / 2))
                    .attr("dy", "1em")
                    .style("text-anchor", "middle")
                    .style({"font-size":font_size, "fill":"#7d7d7d" })
                    .text(yAxisLabel);

                /* Draw line for each types_of_plot  - Data */
                var types_of_plot = svg.selectAll(".types_of_plot")
                    .data(dictionary_for_plotting).enter()
                    .append("g")
                    .attr("class", "types_of_plot");

                // mouse over functionality has been disabled! to be fixed later
                types_of_plot.append("path")
                    .attr("class", "line")
                    .attr("d", function(d,i) {
                        if(is_log)
                        console.log((d.values));
                        return line(d.values);
                    })
                    .style("stroke", function(d,i) { return colorArray(d.name); })
                    .style("fill-opacity", 0)
                    .style("fill","none")
                    .attr("id", function(d) { return d.name; })
                    .on("mouseout", function() { tooltip.style("display", "none"); })
                    .on("mouseover", function(d) {
                        var xPosition = d3.mouse(this)[0],
                            yPosition = d3.mouse(this)[1];

                        tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")")
                            .style({"display": "block"})
                            .attr("fill",function() { return colorArray(d.name); });
                        tooltip.select("text")
                            .text(function(){

                                // printing date value

                                var offsetFactor = width*0.8/ d.values.length;

                                return d.values[Math.floor(xPosition/offsetFactor)].date; });
                    });



                svg.append("g")
                    .attr("class", "axis")
                    .style('fill', 'none')
                    .style('stroke', '#000')
                    .style('shape-rendering',"crispEdges")
                    .attr("transform", "translate(0," + 0.7*height + ")")
                    .style("stroke","#000")
                    //Gives numbers and ticks
                    .call(xAxis);

                // Add the text label for the x axis- height is kinda hardcoded: have to talk with nick
                svg.append("text")
                    .attr("transform", "translate(" + (0.8*width / 2) + " ," + (0.8*height ) + ")")
                    .style("text-anchor", "middle")
                    .style({"font-size":font_size, "fill":"#7d7d7d" })
                    .text(xAxisLabel);

                d3.select("#"+div).select(".x").selectAll(".tick line").style({"opacity": "0", "stroke-width": "0"});

                /* Tooltip, initial display is hidden */
                var tooltip = svg.append("g")
                    .attr("class", "tooltip-multiLine")
                    .style("display", "none");

                var mouseOverOffsetX = -100;
                tooltip.append("rect")
                    .attr("x",mouseOverOffsetX)
                    .attr("y",-25)
                    .attr("width", 165)
                    .attr("height", 20)
                    .attr("rx","5").attr("ry","5")
                    .style("opacity", 1);

                tooltip.append("text")
                    .attr("y",-25)
                    .attr("x", mouseOverOffsetX + 10)
                    .attr("dy", "1.2em")
                    .style("text-anchor", "left")
                    .attr({"font-size":"12px", "fill":"#000"});

                // getting the legends to show up
                var legendYear = svg.selectAll(".legend-year")
                    .data(function(d){
                        return colorArray.domain().slice().reverse();
                    })
                    .enter().append("g")
                    .attr("class", "legend-year")
                    // .attr("transform", "translate(0, 375)");
                    .attr("transform", "translate(0,0)");

                // shape and location of rectangle
                legendYear.append("rect")
                    .attr("x", 0.8*width+5)
                    .attr("y",function(d,i) {
                        return ((0.1*height) - (i*25));
                    })
                    .attr({"width":80,"height": 20})
                    .attr("class", function(d) { return "legend-rect-year-" + d; })
                    .style("fill", colorArray);

                //filling the legends with the right text
                legendYear.append("text")
                    .attr("x", 0.8*width+10)
                    .attr("y",function(d,i) {
                        return ((0.1*height+15) - (i*25));
                    })
                    // .attr("font-weight","bold")
                    .style({"font-size":legend_font_size, "fill":"#000" })
                    .text(function(d) { return d; });

                // getting buttons for log and lin
                var logLinear = svg.selectAll(".logLinear-multiLine")
                    .data(function(d){
                        return linlog.domain().slice(0,2);
                    })
                    .enter().append("g")
//                    .attr("class", "logLinear")
                    .attr("transform", "translate(0, 0)");

                // shape and location of rectangle
                logLinear.append("rect")
                    .attr("x", function(d,i){
                        return 0.8*width+5;
                    })
                    .attr("y", function (d,i) {
                        return 0.7*height-100 - 25*i;
                    })
                    .attr({"width": 50,"height": 20})
//                    .attr("class", function(d) { return "logLinear-" + d; })
                    .style("fill", linlog);

                //filling the legends with the right text
                logLinear.append("text")
                    .attr("x", function(d,i){
                        return 0.8*width+10;
                    })
                    .attr("y",function(d,i){
                        return 0.7*height-85 - 25*i;
                    })
                    .style({"font-size":legend_font_size, "fill":"#000" })
                    .text(function(d) { return d; });

                logLinear.on("click", function(e) {

                    d3.select("#"+div+"svg_multi_line_plot")
                        .remove();


//                    var myElem = document.getElementById(div);
//                    if (myElem == null) {
//                        myElem = document.createElement('div');
//                        myElem.id = div;
//                        document.getElementsByTagName('body')[0].appendChild(myElem);
//                    }

                    var selectedLegend = d3.select(this).text();

                    if(selectedLegend == "log"){
                        render_plot(myDataSource,raw_data, true);
                    }
                    else{
                        render_plot(myDataSource,raw_data, false);
                    }

                });

            };


            /* Load chart data */
            var loadChartData = function(dataSource,raw_data,xLabel,yLabel){
                drawData(dataSource,raw_data,xLabel, yLabel);
            };

            // tick text format
            var formatMonthTicks = function(tickDivider){
                d3.select("#"+div).select(".x").selectAll(".tick text").each(function(d,i) {
                    i++;
                    if (i%tickDivider !==0) { d3.select(this).style("opacity", 0); }
                });
            }

            loadChartData(dataSource,raw_data,xLabel,yLabel);
        };
    }


    // all log stuff has been commented out
    data.make_stacked_array_chart = function(data_in, div, label, height, width) {

        var drawData= function(dataSource,raw_data,div, is_log){

            var data = dataSource.data;

            var margin = {top: 0.1*height, right: 0.1*width, bottom: 140, left: 0.1*width};

            var parseDate = d3.time.format("%y-%b-%d").parse,

                formatPercent = d3.format(".0%");

            var x = d3.scale.linear()
                .range([0, 0.8*width]);


            var y;
            if(is_log){
                y= d3.scale.log()
                    .range([0.7*height, 0])

            }
            else{
                y= d3.scale.linear()
                    .range([0.7*height, 0]);
            }

            var color = d3.scale.ordinal().range(colorsChart);//d3.scale.category20();

            var linlog  = d3.scale.ordinal().domain(["linear","log"]);
            linlog.range(buttonsChart);

            var xAxis = d3.svg.axis()
                .tickFormat(d3.format(",.2f"))
                .scale(x)
                .orient("bottom")
                .tickFormat(function(d) {
                    // body...
                    return d;
                });

            var yAxis = d3.svg.axis()
                .scale(y)
                .ticks(20,(",.2f"))
                .orient("left");

	    if(is_log){
		yAxis =d3.svg.axis()
		    .scale(y)
		    .orient("left");
	    }
	    
            var line = d3.svg.line()
                .x(function(d) {  return x(d.date); })
                .y(function(d) {
                    return y(d.y0 + d.y);
                });

            var area = d3.svg.area()
                .x(function(d) { return x(d.date); })
                .y0(function(d,i) {
                    return y(d.y0);
                })
                .y1(function(d) { return y(d.y0 + d.y); });

            if(is_log){
                //giving it an offset for the log plot
                var stack = d3.layout.stack()
                    .offset(function(d){

                        var j = -1,
                            m = d[0].length,
                            y0 = [];
                        while (++j < m) y0[j] = 0.01;
                        return y0;
                    })
                    .values(function(d) { return d.values; });

            }
            else{
                var stack = d3.layout.stack()
                    .values(function(d) { return d.values; });

            }


	    //var randomSvgId = Math.floor(Math.random()*10000)+1);
            var svg = d3.select("#"+div).append("svg")
                .attr("id", div+"svg_area")
                .attr("width", width)
                .attr("height", 1.15*height)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            /* Chart title */
            svg.append("text")
                .attr("class", "title")
                .attr("x", 174).attr("y", -25).attr("text-anchor", "middle")
                .style({"font-size":font_size, "fill":"#7d7d7d" })
                .text(label);

            // going through key values of first dict object and picking all the keys to that will be stacked
            color.domain(d3.keys(data[0]).filter(function(key) { return key !== "x"  && key!== "t"; }));

            var post_stacked_layout = stack(color.domain().map(function(name) {
                return {
                    name: name,
                    values: data.map(function(d) {

                        if(!is_log ){
                            return {date: d.x, y: d[name], timeStamp : d.t};

                        }

                        else{
                            var y=0;
                            if(d[name] !=0){

//                                y=Math.log10(d[name]);
                                  y = d[name];


                            }
                            else{
                                // setting to a high value
                                y = 0.0001;
                            }
                            return {date: d.x, y:y, timeStamp : d.t};
                        }

                    })
                };
            }));

            x.domain([0,raw_data.x_max]);

            if(!is_log){
                y.domain([raw_data.y_min,3*raw_data.y_max]);
            }
            else{
//                y.domain([raw_data.data.length*dataSource.min_log_y,raw_data.data.length*dataSource.max_log_y]);
                  y.domain([0.01,3*raw_data.y_max]);

            }

            var post_stacked_layout = svg.selectAll(".post_stacked_layout")
                .data(post_stacked_layout)
                .enter().append("g")
                .attr("class", "post_stacked_layout");

            // getting the legends to show up
            var legendYear = svg.selectAll(".legend-year-area")
                .data(function(d){
                    return color.domain().slice().reverse();
                })
                .enter().append("g")
//                .attr("class", ".legend-year-area")
                .attr("transform", "translate(0, 0)");

            /* Tooltip, initial display is hidden */
            var tooltip = svg.append("g")
                .attr("class", "tooltip")
                .style("display", "none");

            var mouseOverOffsetX = -65;
            tooltip.append("rect")
                .attr("x",mouseOverOffsetX)
                .attr("y",-25)
                .attr("width", 165)
                .attr("height", 20)
                .attr("rx","5").attr("ry","5")
                .style("opacity", 1);

            tooltip.append("text")
                .attr("y",-25)
                .attr("x", mouseOverOffsetX + 10)
                .attr("dy", "1.2em")
                .style("text-anchor", "left")
                .attr({"font-size":"12px", "fill":"#000"});

            // shape and location of rectangle
            legendYear.append("rect")
                .attr("x", 0.8*width+10)
                .attr("y",function(d,i) {
                    return ((0.2*height) - (i*25));
                })
                .attr({"width": 70,"height": 20})
                .style("fill", color);

            //filling the legends with the right text
            legendYear.append("text")
                .attr("x", 0.8*width+15)
                .attr("y",function(d,i) {
                    return (0.2*height+15) - (i*25);
                })
                .style({"font-size":legend_font_size, "fill":"#000" })
                .text(function(d) { return d; });

//             LIN LOG FEATURE FOR STACKED stuff ( COMMENTED OUT: DOES NOT WORK FOR NOW, to do later)

            var logLinear = svg.selectAll(".logLinear-area")
                .data(function(d){
                    return linlog.domain().slice(0,2);
                })
                .enter().append("g")
//                .attr("class", "logLinear-area")
                .attr("transform", "translate(0, 0)");

            // shape and location of rectangle
            logLinear.append("rect")
                .attr("x", function(d,i){
                    return 60*i +10;
                })
                .attr("y",0)
                .attr({"width": 50,"height": 20})
                .style("fill", linlog);

            //filling the legends with the right text
            logLinear.append("text")
                .attr("x", function(d,i){
                    return 60*i +15;
                })
                .attr("y",15)
                .style({"font-size":legend_font_size, "fill":"#000" })
                .text(function(d) { return d; });

            logLinear.on("click", function(e) {
//                var xPos = +(d3.select(this).select("rect").attr("x")) + 14;
                d3.select("#"+div+"svg_area").remove();

                var selectedLegend = d3.select(this).text();

                if(selectedLegend == "log"){
                    loadChart(plotData,data_in,div,true);
                }
                else{
                    loadChart(plotData,data_in,div,false);
                }

            });


            post_stacked_layout.append("path")
                .attr("class", "area")
                .attr("d", function(d) { return area(d.values); })
                .style("fill", function(d) { return color(d.name); })
                .on("mouseout", function() { tooltip.style("display", "none"); })
	        .on("mousedown", function(d) {
		    var xPosition = d3.mouse(this)[0],
			yPosition = d3.mouse(this)[1];

		   
		   
		    tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")")
		        .style({"display": "block"})
		        .attr("fill",function() { return color(d.name); });
		    tooltip.select("text")
		        .text(function(){

			    // printing date value

			    var offsetFactor = width*0.8/ d.values.length;
			    console.log(d.values[Math.floor(xPosition/offsetFactor)].timeStamp);
			    return d.values[Math.floor(xPosition/offsetFactor)].timeStamp; });
		});
            ;

            post_stacked_layout.append("path")
                .attr("class", "line")
                .attr("d", function(d) {
                    return line(d.values);
                })
                .style("stroke", "#000")
                .style("fill", "none")
            ;


            svg.append("g")
                .attr("class", "x axis")
                .style('fill', 'none')
                .style('stroke', '#000')
                .style('shape-rendering',"crispEdges")
                .attr("transform", "translate(0," + 0.7*height + ")")
                .call(xAxis);



            svg.append("g")
                .attr("class", "y axis")
                .style('fill', 'none')
                .style('stroke', '#000')
                .style('shape-rendering',"crispEdges")
                .call(yAxis);

            // Add the text label for the x axis- height is kinda hardcoded: have to talk with nick
            svg.append("text")
                .attr("transform", "translate(" + (0.8*width / 2) + " ," + (0.8*height ) + ")")
                .style("text-anchor", "middle")
                .style({"font-size":font_size, "fill":"#7d7d7d" })
                .text(raw_data.x_label);

            // Add the text label for the Y axis
            svg.append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", 0- 55)
                .attr("x",0 - (0.7*height / 2))
                .attr("dy", "1em")
                .style("text-anchor", "middle")
                .style({"font-size":font_size, "fill":"#7d7d7d" })
                .text(raw_data.y_label);
        };

        var loadChart = function(data_source,raw_data,div, is_log){

            drawData(data_source,raw_data,div,is_log);

        };

        var plotData = data.format_data_for_stacked_area_chart(data_in);
        loadChart(plotData,data_in,div,false);



    }


    data.plot = function(dataSource,divIDName,label){

        // check if div exists
        var myElem = document.getElementById(divIDName);

        if (myElem == null) {
            myElem = document.createElement('div');
            myElem.id = divIDName;
            document.getElementsByTagName('body')[0].appendChild(myElem);

        }

	if(dataSource.data.length == 0){
	    $('#'+divIDName).html("<p><b> No data available to be plotted </b></p>");
	}

        if(dataSource.plot_type == 'stacked_area_plot'){
            data.make_stacked_array_chart(dataSource,divIDName,label, myElem.offsetHeight, myElem.offsetWidth);
        }
        else if(dataSource.plot_type == 'histogram'){
            data.make_histogram(dataSource,divIDName,label, .6*myElem.offsetHeight, myElem.offsetWidth);
        }

        else if(dataSource.plot_type=='multi_line_plot'){
            data.make_multi_line_chart(dataSource,divIDName,label, myElem.offsetHeight, myElem.offsetWidth);
        }
    }

    data.createDynamicTable = function(data, div_id) {
        """
        Requires data and a div id to to populate the data into a table dynamically.

        Usage: ::\n        
        Example input is:
            {'plot_type': 'columnar_table', 'meta': {'status': 'OK', 'code': 200}, 'data': [{'index': 0, 'target': {'target_id': 0, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 0, 'alt_description': 0}, 'rank': 0}, {'index': 2, 'target': {'target_id': 2, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 2, 'alt_description': 2}, 'rank': 1}, {'index': 3, 'target': {'target_id': 3, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 3, 'alt_description': 3}, 'rank': 2}, {'index': 4, 'target': {'target_id': 4, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 4, 'alt_description': 4}, 'rank': 3}, {'index': 6, 'target': {'target_id': 6, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 6, 'alt_description': 6}, 'rank': 4}, {'index': 5, 'target': {'target_id': 5, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 5, 'alt_description': 5}, 'rank': 5}, {'index': 1, 'target': {'target_id': 1, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 1, 'alt_description': 1}, 'rank': 6}, {'index': 8, 'target': {'target_id': 8, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 8, 'alt_description': 8}, 'rank': 7}, {'index': 9, 'target': {'target_id': 9, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 9, 'alt_description': 9}, 'rank': 8}, {'index': 7, 'target': {'target_id': 7, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 7, 'alt_description': 7}, 'rank': 9}]}
        """

        if(data.data.length == 0){
          $('#'+div_id).html("<h1 style='text-align:center'> No data to rank </h1>");
        }else if(data.plot_type == 'columnar_table'){
            $('#'+div_id).html('<table class="table table-bordered" style="text-align:center;vertical-align:middle;"><thead><tr></tr></thead><tbody></tbody></table>');
            var head = $('#'+div_id+' thead tr');
            // loop through headers
            for (var i=0; i < data.headers.length; i++){
                head
                    .append($('<th>')
                        .html(data.headers[i].label)
                    )
            }
            var body = $('#'+div_id+' tbody');
            for (var i = 0; i < data.data.length; i++) {
                body.append($('<tr>'));
                for (var j=0; j<data.headers.length; j++){
                    var current_row = $('#'+div_id+' tbody tr:nth-child('+(i+1)+')');
                    if (data.headers[j].field == 'index' && data.data[i]['target']){
                        target = data.data[i].target;
                        if(target.primary_type == 'image'){
                            current_row
                                .append($('<td>')
                                    .append($('<img>')
                                        .attr('src', target.primary_description)
                                        .css({'max-height':'100px','width':'auto'})
                                    )
                                )
                        }else{
                            current_row
                                .append($('<td>')
                                    .html(target.primary_description)
                                )
                        }
                    }else{
                        current_row
                            .append($('<td>')
                                .html(data.data[i][data.headers[j].field])
                            )
                    }
                }
            }
        }
    }

}) (this.charts = {});
  
