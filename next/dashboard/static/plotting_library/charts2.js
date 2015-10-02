var colorsChart = [["#31a354"],["#3182bd"],["#756bb1"],["#636363"],["#c70076"],["#45bdbd"],["#"],["#"]];

var buttonsChart = [["#A9A9C6"]];

(function(data) {

    var font_size = 14;
    var legend_font_size = 13;
    var previousSelected; // global to show both log and linear in show mode

    //defines a function to be used to append the title to the tooltip.  you can set how you want it to display here.
    var format = d3.time.format("%Y-%m-%d %X %L");

    /**
     *  function to get date in the right format
     * @param timeData - array of time stamps
     * @returns {formatted time stamp based on formate declared above}
     */
    var getDateFormat = function(timeData){

        // format of time stamp in data

        // A formatter for counts.
        var formatCount = d3.format(",.0f");
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
    /**
     *  function to generate d3 histogram layout
     * @param num_bins - number of bins for histogram
     * @param format - time format for data
     * @param data_to_be_plotted - formatted data for histogram
     * @returns {histogram_layout- a d3 histogram layout
     */
    var generate_histogram_layout = function(num_bins, format, data_to_be_plotted, type,x){
        // Generate a histogram using "num_bins" uniformly-spaced bins.
        var histogram_layout;
        if(type == "histogram"){

            histogram_layout = d3.layout.histogram()
                .bins(num_bins)
                .value(function (d) {

                    return format.parse(d).getTime()
                })
                .range([format.parse(d3.min(data_to_be_plotted, function(d){ return d})),
                    format.parse(d3.max(data_to_be_plotted, function(d){ return d}))])
            (data_to_be_plotted);
        }

        else{
//            histogram_layout = d3.layout.histogram()
//                .bins(num_bins)
////                .range([(d3.min(data_to_be_plotted, function(d){ return d})),
////                    (d3.max(data_to_be_plotted, function(d){ return d}))])
//            (data_to_be_plotted);

            histogram_layout = d3.layout.histogram()
                                .bins(x.ticks(num_bins))
                                (data_to_be_plotted);
        }

        return histogram_layout;
    }


    /**
     * Draws a histogram on the svg canvass
     * @param div - the div to which we attach svg
     * @param width - width of the svg
     * @param height - height of the svg
     * @param margin - margins of canvas
     * @param label - chart title
     * @param data - histogram_layout object
     * @param data_in - raw json data passed in
     * @param x - x axis scale
     * @param y - y axis scale
     * @param yAxis - y Axis d3 axis object
     * @param xAxis - x Axis d3 axis object
     * @param formatCount -A formatter for counts for the time
     */
    var draw_time_histogram = function(div, width, height, margin, label, data, data_in, x, y, xAxis, yAxis, formatCount){

        var svg = d3.select("#"+div).append("svg")
            .attr("id",div+"svg_histogram")
            .attr("width", width)
            .attr("height", 1.4*height)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

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
            .attr("transform", function(d) {
                return "translate(" + x(d.x) + "," + (y(d.y)) + ")";
            });

        // the bar
        bar.append("rect")
            .data(data)
            .attr("y", function(d) { return 0; })
            .attr("x",0)
            .attr("stroke", "#FFF")
            .attr("fill", colorsChart[2])
            .attr("width", function(d) {
                return x(d.x+d.dx)-x(d.x);
            })
            .attr("height", function(d) {
                return height - y(d.y);
            });

//        // text
//        bar.append("text")
//            .attr("y", -5)
//            .attr("x", function(d) { return (x(d.x+d.dx)-x(d.x))/2 })
//            .attr("text-anchor", "middle")
//            .attr("fill","black")
//            .text(function(d) {
//                return formatCount(d.y);
//            });

        svg.append("g")
            .attr("class", "y axis")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style('shape-rendering', 'crispEdges')
            .style({"font-size":font_size-5, "font-family": "Times New Roman" })
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
//            .style("font-size","10px")
            .style('shape-rendering', 'crispEdges')
            .attr("transform", "translate("+ 0 +"," + height + ")")
            .style({"font-size":font_size-5, "font-family": "Times New Roman" })
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
            .attr("transform", "translate(" + (width - 105) + " ," + (height + margin.bottom-20) + ")")
            .style({"font-size":font_size - 5, "fill":"#7d7d7d" })
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

    /**
     * Formats histogram data into a dictionary ready to be plotted
     * @param data_in - the raw JSON object passed in
     * @returns {{data_to_be_plotted: the data which will be plotted
     * }}
     */
    var format_data_for_histogram = function (data_in) {
        // the data we are plotting
        var data_to_be_plotted = [];

        for(var i = 0, j=0; i< data_in.data.t.length-1; i++){
            if(getDateFormat(data_in.data.t[i]) != -1){
                data_to_be_plotted[j++] = getDateFormat(data_in.data.t[i]);
            }
        }

        return data_to_be_plotted;
    }
    /**
     * Draws clickable legends for the graph
     * @param svg - the svg canvas we attach legends too
     * @param keys - list of names for legend labels
     * @param width - width of svg
     * @param height - height of svg
     */
    var make_legends = function(svg,keys,width,height) {

        var number_of_legends_per_row =2;

        // getting the legends to show up
        var legend = svg.selectAll(".legend")
            .data(function(d){
                return keys.domain();
            })
            .enter().append("g")
            .attr("class", "legend")
            // .attr("transform", "translate(0, 375)");
            .attr("transform", "translate(0,0)");

        // shape and location of rectangle
        legend.append("rect")
            .attr("x", function(d,i){
                return (i%number_of_legends_per_row)*width/2.5 ;
            })
            .attr("y",function(d,i) {
                return (height- 0.2*height) + (Math.floor(i/number_of_legends_per_row))*25 +5 ;
                // return ((0.7*height) - (i*25));

            })
            .attr({"width":10,"height": 20})
            .attr("class", function(d) { return "legend-rect-year-" + d; })
            .style("fill", keys);

        //filling the legends with the right numbers so i can click em
        legend.append("text")
            .attr("x", function(d,i){
                return (i%number_of_legends_per_row)*width/2.5 + 15;
            })
            .attr("y",function(d,i) {
                return (height- 0.2*height) + (Math.floor(i/number_of_legends_per_row))*20 +20;

            })
            .style("font-size",10)
            .style("fill","#000" )
            .text(function(d,i) {
                return d;
            });

        // print name of legend label    
        legend.on("click", function(e) {

            var selectedLegend = d3.select(this).text();

            d3.select("#legend_label").remove();

            var legend_label = svg.append("g")
                .attr("id", "legend_label")
                .attr("class", "legend_label")
                .attr("transform", "translate(0, 0)");

            legend_label.append("text")
                .attr("x", 45)
                .attr("y",height- 0.2*height + 15)
                .style("font-size",legend_font_size)
                .style("fill","#000" )
                .text(keys.domain()[selectedLegend]);

        });
    }

    /**
     * Makes two buttons for linear and log scales
     * @param svg - the svg canvas on which we draw buttons
     * @param linlog - domain and range for the buttons
     * @param width - width of svg
     * @param height - height of svg
     * @returns {{loglinear: two clickable buttons to change scale of graph
     * }}
     */
    var make_lin_log_button = function(svg, linlog, width, height){

        // getting buttons for log and lin
        var logLinear = svg.selectAll(".logLinear")
            .data(function(d){
                return linlog.domain().slice(0,2);
            })
            .enter().append("g")
            .attr("class", "logLinear")
            .attr("transform", "translate(0, 0)");

        // shape and location of rectangle
        logLinear.append("rect")
            .attr("x", function(d,i){
                return 60*i+5;
            })
            .attr("y", function (d,i) {
                return 0;
            })
            .attr({"width": 50,"height": 20})
            .style("fill", linlog);

        //filling the legends with the right text
        logLinear.append("text")
            .attr("x", function(d,i){
                return 60*i+15;
            })
            .attr("y",function(d,i){
                return 15;
            })
            .style({"font-size":legend_font_size, "fill":"#000" })
            .text(function(d) { return d; });

        return logLinear;
    }

    /**
     * Draws x and y axis on the svg canvas
     * @param svg - the svg canvas on which we draw buttons
     * @param yAxis - property function of y axis
     * @param xAxis - property function of x axis
     * @param width - width of the svg
     * @param height - height of the svg
     * @param yAxisLabel - Y axis label
     * @param xAxisLabel - X axis label
     */
    var draw_Axes = function(svg, yAxis, xAxis, width, height, yAxisLabel, xAxisLabel){

        // physically drawing y axis
        svg.append("g")
            .attr("id","yAxis")
            .attr("class", "y_Axis")
            .style('fill', 'none') // keeps axis lines thin
            .style('stroke', '#000') // gives axis line color (black)
            .style('shape-rendering',"crispEdges")
            .style({"font-size":font_size-5, "font-family": "Times New Roman" })
            .call(yAxis)

        ;


        // Add the text label for the Y axis
        svg.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0- 45)
            .attr("x",0 - (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .style({"font-size":font_size-5,"font-family": "Times New Roman", "fill":"#7d7d7d" });
        // .text(yAxisLabel); // commented out on advise from Lalit

        // drawing the x axis
        svg.append("g")
            .attr("id","xAxis")
            .attr("class", "xAxis")
            .style('fill', 'none')
            .style('stroke', '#000')
            .style('shape-rendering',"crispEdges")
            .attr("transform", "translate(0," + 0.7*height + ")")
            .style("stroke","#000")
            .style({"font-size":font_size-5, "font-family": "Times New Roman" })
        //Gives numbers and ticks
            .call(xAxis);

        // Add the text label for the x axis- height is kinda hardcoded: have to talk with nick
        svg.append("text")
//            .attr("transform", "translate(" + (0.8*width / 2) + " ," + (0.8*height ) + ")")
            .attr("transform" , "rotate(0)")
            .attr("x", 0.8*width/2)
            .attr("y",function(d,i) {
                return ((height- 0.2*height) );

            })
            .style("text-anchor", "middle")
            .style({"font-size":font_size-5,"font-family": "Times New Roman", "fill":"#7d7d7d" })
            .text(xAxisLabel);

    }

    /**
     * Makes a rectangular tooltip that reveals data on mouse hover
     * @param svg - the svg canvas on which we draw buttons
     (Currently not using a tooltip)
     */
    var make_tooltip = function(svg){

        var tooltip = svg.append("g")
//            .attr("x",0)
//            .attr("y",0)
            .attr("class", "tooltip")
            .style("display", "none");

        var mouseOverOffsetX = 0;
        tooltip.append("rect")

            .attr("width", 220)
            .attr("height", 20)
            .attr("rx","5").attr("ry","5")
            .style("opacity", 1);

        tooltip.append("text")
//            .attr("y",-25)
//            .attr("x", mouseOverOffsetX + 10)
            .attr("dy", "1.2em")
            .style("text-anchor", "left")
            .attr({"font-size":"12px", "fill":"#000"});

        return tooltip;
    }

    /**
     * Creates a svg canvas
     * @param div - the div to which we attach svg
     * @param width - width of the svg
     * @param height - height of the svg
     * @param margin - margins of canvas
     * @param chart_title - property function of x axis
     * @param type_of_plot - Y axis label
     * @returns {{svg: a svg canvas
     * }}
     */
    var create_svg = function (div,width, height, margin, chart_title, type_of_plot) {

        var svg = d3.select("#"+div).append("svg")
            .attr("id", div+type_of_plot)
            .attr("width", width)
            .attr("height", 1.15*height)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        /* Chart title */
        svg.append("text")
            .attr("class", "title")
            .attr("x", (width/3.2))
            .attr("y", -25)
            .attr("text-anchor", "middle")
            .style({"font-size":font_size, "fill":"#7d7d7d" })
            .text(chart_title);

        return svg;
    }

    /**
     * Creates a line object which contains the logic for line path for multi-line plot
     * @param x - scale of the x axis
     * @param y - scale of the y axis
     * @returns {{line: line object that gives x and y coordinates for path of lines on the graph
     * }}
     */
    var line_function = function(x,y){

        var line = d3.svg.line()
            .x(function(d) {
                return x(d.x_val);
            })
            .y(function(d) {
                return y(d.y_val);
            });

        return line;
    }

    /**
     * Draws lines on the svg canvas based on line object
     * @param type - type of plot ("stacked_area" or "multiline")
     * @param plot - the plot layout object of the svg we append lines to
     * @param line - line object that gives x and y coordinates for path of line
     * @param tooltip - ( for multi line only)the tooltip that lets us inspect points on graph
     * @param keys - ( for multi line only array containing legend labels
     * @param width - ( for multi line only width of svg canvas
     * @returns {{svg: a svg canvas
     * }}
     */
    var draw_lines = function(type,plot,line, tooltip, keys, width){


        if(type == "stacked_area"){
            plot.append("path")
                .attr("class", "line")
                .attr("d", function(d) {
                    return line(d.values);
                })
                .style("stroke", "#000")
                .style("fill", "none");
        }

        if(type == "multiline")
            plot.append("path")
                .attr("class", "line")
                //here's where the lines are drawn
                .attr("d", function(d,i) {
                    return line(d.values);
                })
                .style("stroke", function(d,i) { return keys(d.name); })
                .style("fill-opacity", 0)
                .style("fill","none")
                .attr("id", function(d) { return d.name; })
                .on("mouseout", function() { tooltip.style("display", "none"); })

    }

    /**
     * Defines the scale (domain and range) for the x axis
     * @param raw_data - the raw JSON object passed in
     * @param width - width of svg canvas
     * @param data_to_be_plotted - formatted histogram data( only for histogram)
     * @returns {{x: the scale for the x axis
     * }}
     */
    var make_x_scale = function(raw_data, width, data_to_be_plotted){

        var x;
        // format of time stamp in data ( only for histogram )
        var format;
        if(raw_data.plot_type == "histogram"){
            format = d3.time.format("%Y-%m-%d %X %L");
            // setting up x axis domain and range
            x = d3.time.scale()
                .domain([format.parse(d3.min(data_to_be_plotted, function(d){ return d})),
                    format.parse(d3.max(data_to_be_plotted, function(d){ return d}))])
                .range([0, 0.8*width])
                .nice(.8*width);

        }
        else if(raw_data.plot_type == "histogram_real"){

            x = d3.scale.linear()
                .domain([
                    d3.min(data_to_be_plotted) - 0.001,
                    d3.max(data_to_be_plotted) + 0.001
                ])
                .range([0, width]);


        }
        else{
            x = d3.scale.linear()
                .domain([0, raw_data.x_max])
                .range([0, 0.8*width]);

        }

        return x;
    }

    /**
     * Defines the range for the y axis
     * @param is_log - type of scale ( log or linear)
     * @param height - height of svg canvas
     * @param plot_type - type of plot
     * @param histogram_layout - (only for histogram) histogram layout
     * @returns {{y: the scale for the y axis
     * }}
     */
    var make_y_scale = function(is_log, height, plot_type, histogram_layout){

        var y;
        if(plot_type == "histogram" || plot_type == "histogram_real"){
            y = d3.scale.linear()
                .domain([0, d3.max(histogram_layout, function(d) { return d.y; })])
                .range([height, 0 ]);

        }
        else{
            if(!is_log){
                y= d3.scale.linear()
                    .range([0.7*height, 0])

            }
            else{
                y= d3.scale.log()
                    .range([0.7*height, 0]);
            }

        }

        return y;
    }

    /**
     * Define properties of the x axis
     * @param x - scale of x axis
     * @param plot_type - type of plot
     * @param width - width of div
     * @param num_bins - (only for histogram) number of bins
     * @returns {{xAxis: d3.axis object
     * }}
     */
    var make_x_axis = function(x, plot_type,width, num_bins){

        // define x axis
        var xAxis;

        // number of ticks : eyeballed this scaling (no real math)
        var number_of_ticks = Math.floor(width/50);

        if(plot_type != "histogram"){
            xAxis = d3.svg.axis()
                .scale(x)
//                .tickFormat(d3.format(",.2f"))
                .orient("bottom")
                .ticks(number_of_ticks)
                .tickFormat(function(d){  return d ; })

        }

        // histogram
        else{
            xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .ticks(number_of_ticks)
                .tickFormat(d3.time.format("%m-%d-%y %X"));

        }

        return xAxis;
    }

    /**
     * Define properties of the y axis
     * @param y - scale of y axis
     * @param is_log - type of plot (log or linear)
     * @param height - height of div
     * @param plot_type - type of plot
     * @returns {{yAxis: d3.axis object
     * }}
     */
    var make_y_axis = function(y, is_log,height, plot_type){

//        var superscript = "⁰¹²³⁴⁵⁶⁷⁸⁹";
//        var formatPower = function(d){
//            return (d + "").split("").map(function(c) { return superscript[c];
//        }

        var yAxis;
        var number_of_ticks = height/50;
        if(plot_type == "histogram" || plot_type == "histogram_real" ){
            yAxis = d3.svg.axis()
                .scale(y)
                .orient("left");

        }
        else{
            yAxis = d3.svg.axis()
                .scale(y)
                .ticks(number_of_ticks)
                .tickFormat(d3.format(",.2f"))
                .orient("left");

            if(is_log){
                yAxis = d3.svg.axis()
                    .scale(y)
//                    .tickFormat(function(d,i) {
//
////                        var format = d3.format("s")
//                        if(i%10 == 0)
//                            return format(d);
//                    })
                    .ticks(number_of_ticks)
                    .orient("left");
                ;
            }

        }


        return yAxis;
    }

    /**
     * Creates an array of the legend labels
     * @param raw_data - the raw JSON object passed in
     * @returns {{keys: an array of legend labels
     * }}
     */
    var keys_for_multiline_data = function(raw_data){

        // setting up keys ( different legend labels)
        var keys = d3.scale.ordinal().range(colorsChart);
        var keys_domain =[];
        raw_data.data.map(function(d){
            keys_domain.push(d["legend_label"])
        });
        keys.domain(keys_domain);

        return keys;
    }

    /**
     * Creates range and domain for log and linear buttins
     * @returns {{linlog: an object which contains the range and domain of the linear log buttons
     * }}
     */
    var range_and_domain_for_linlog_buttons = function(){
        // range and domain for buttons for linear and log option
        var linlog  = d3.scale.ordinal().domain(["linear","log"]);
        linlog.range(buttonsChart);

        return linlog;
    }

    /**
     * Formats multiline data into a dictionary ready to be plotted
     * @param raw_data - the raw JSON object passed in
     * @returns {{data_to_be_plotted: the data which will be plotted
     * }}
     */
    var fomat_data_for_multiline_plot = function(raw_data){

        var data_to_be_plotted = raw_data.data.map(function (d){
            return {
                name : d["legend_label"],
                values: d.x.map(function (d1,i){
                    return {x_val: d.x[i], y_val: d.y[i] ,date : d.t[i]};
                })
            };

        });

        return data_to_be_plotted;
    }

    /**
     * Appends data to the svg object
     * @param svg - the svg canvas
     * @param data - formatted data ready to be plotted
     * @param class_name - css class of this svg data object
     * @param x - x scale
     * @param y - y scale
     * @param keys - variable that holds domain and range of legends labels
     * @param width - width of svg
     * @param height - height
     * @param plot_type - type of plot
     * @returns {{types_of_plot: an svg object with data appended to it
     * }}
     */
    var append_data_to_svg = function(svg ,data, class_name, x, y, keys, width, height, plot_type){

        var opacity_of_circles =1e-6 , radius_of_circle=3;

        // appending date to the svg
        var types_of_plot = svg.selectAll("."+class_name)
            .data(data).enter()
            .append("g")
            .attr("class", class_name);

        // draw invisible circles on the points so i can hover over them    
        types_of_plot.selectAll("circle")
            .data( function(d) {return(d.values);} )
            .enter()
            .append("circle")
            // .attr("class","tipcircle")
            .attr("cx", function(d,i){
                if(plot_type == "multi_line_plot"){
                    return x(d.x_val);
                }
                // stacked area plot
                else{
                    return x(d.date);
                }
            })
            .attr("cy",function(d,i){
                if(plot_type == "multi_line_plot"){
                    return y(d.y_val);
                }

                // stacked area plot
                else{
                    return y(d.y + d.y0);
                }
            })
            .attr("r",radius_of_circle)
            .style('opacity', opacity_of_circles)//1e-6
            .attr("id", function(d) { return d.name; })
            .on("mouseout", function() {
                d3.select("#mouseHoverDate")
                    .remove();
                d3.select("#mouseHoverYandXVal")
                    .remove();
            })
            .on("mouseover", function(d) {
                var xPosition = d3.mouse(this)[0],
                    yPosition = d3.mouse(this)[1];


                d3.select("#mouseHoverDate")
                    .remove();

                var date_text = "";
                var y_and_x_text = "";
                if(plot_type == "multi_line_plot"){
                    date_text = d.date;
                    y_and_x_text = "y= "+d.y_val.toFixed(5)+", x= "+ d.x_val;

                }
                else{
                    date_text = d.timeStamp;
                    y_and_x_text = "y= "+(d.y + d.y0).toFixed(5)  +", x= "+ d.date;
                }

                var mouseHoverDate = svg.append("g")
                    .attr("id", "mouseHoverDate")
                    .attr("class", "mouseHoverDate")
                    .attr("transform", "translate(0, 0)");;

                mouseHoverDate.append("text")
                    .attr("x", 0.05*width)
                    .attr("y",40)
                    .style({"font-size":legend_font_size, "fill":"#000" })
                    .text(date_text);

                // code duplication because svg.append text doesn't allow
                // multi line text      
                var mouseHoverXandY = svg.append("g")
                    .attr("id", "mouseHoverYandXVal")
                    .attr("class", "mouseHoverYandXVal")
                    .attr("transform", "translate(0, 0)");;

                mouseHoverXandY.append("text")
                    .attr("x", 0.05*width)
                    .attr("y",60)
                    .style({"font-size":legend_font_size, "fill":"#000" })
                    .text(y_and_x_text);
            });



        return types_of_plot;
    }

    /**
     * Set the domain for the y axis
     * @param raw_data - the raw JSON object passed in
     * @param is_log - type of plot (log or linear)
     * @param y - scale for the y axis
     * }}
     */
    var set_y_domain = function(raw_data, is_log, y){


        if(!is_log){
            y.domain([ 0.0, 1.5*raw_data.y_max ]);
        }
        else{
            y.domain([ Math.max(0.5*raw_data.y_min,0.000001), 1.5*raw_data.y_max ]);
        }

    }

    /**
     * Creates a line object which contains the logic for line path for stacked-area plot
     * @param x - scale of the x axis
     * @param y - scale of the y axis
     * @returns {{line: line object that gives x and y coordinates for path of lines on the graph
     * }}
     */
    var area_chart_line = function(x,y){

        var line = d3.svg.line()
            .x(function(d) {  return x(d.date); })
            .y(function(d) {
                return y(d.y0 + d.y);
            });

        return line;
    }

    /**
     * Creates a area object which contains the logic for area fill for stacked-area plot
     * @param x - scale of the x axis
     * @param y - scale of the y axis
     * @returns {{area: area object that gives x and y coordinates for path of area fill on the graph
     * }}
     */
    var area_chart_area = function(x, y){
        var area = d3.svg.area()
            .x(function(d) { return x(d.date); })
            .y0(function(d,i) {
                return y(d.y0);
            })
            .y1(function(d) { return y(d.y0 + d.y); });

        return area;
    }


    /**
     * Define the stack layout for a plot
     * @param is_log - liear or log plot
     * @returns {{stack: object with definition of stack layout
     * }}
     */
    var make_stack_layout = function(raw_data,is_log){

        if(is_log){
            //giving it an offset for the log plot
            var stack = d3.layout.stack()
                .offset(function(d){

                    var j = -1,
                    m = d[0].length,
                    y0 = [];
                    while (++j < m) y0[j] = Math.max(0.5*raw_data.y_min,0.000001);
                    return y0;
                })
                .values(function(d) { return d.values; });

        }
        else{
            var stack = d3.layout.stack()
                .values(function(d) { return d.values; });

        }

        return stack;

    }

    /**
     * Creates an array of the legend labels
     * @param raw_data - the raw JSON object passed in
     * @returns {{keys:  array of legend labels
     * }}
     */
    var make_keys_for_stacked_area_chart = function(raw_data){

        var keys = d3.scale.ordinal().range(colorsChart);
        var keys_domain =[];
        raw_data.data.map(function(d){
            keys_domain.push(d["legend_label"])
        });
        keys.domain(keys_domain);

        return keys;
    }

    /**
     * Formats stacked data into a dictionary ready to be plotted
     * @param raw_data - the raw JSON object passed in
     * @returns {{data_to_be_plotted: the data which will be plotted
     * }}
     */
    var format_data_for_stacked_area_chart = function(raw_data, stack, is_log){

        var data_to_be_plotted = stack(raw_data.data.map(function (d){
            return {
                name : d["legend_label"],
                values: d.y.map(function (d1,i){
                    if(is_log){
                        return {date: raw_data.x[i],
                            y: d.y[i] ,
                            timeStamp : raw_data.t[i]
                        };
                    }

                    else{
                        var y;
                        if(d.y[i] != 0)
                            y = d.y[i];

                        else
                            y=0.0001

                        return {date: raw_data.x[i],
                            y: y ,
                            timeStamp : raw_data.t[i]
                        };

                    }

                })

            };

        }));

        return data_to_be_plotted;
    }

    /**
     * Fills area on the svg canvas based on the area object
     * @param stacked_area_plot - the svg object with formatted data attached to it
     * @param tooltip - ( for multi line only)the tooltip that lets us inspect points on graph
     * @param area - the area object which defines the logic for the fill
     * @param keys - ( for multi line only array containing legend labels
     * @param width - ( for multi line only width of svg canvas
     * }}
     */
    var draw_area_for_stacked_area_plot = function(stacked_area_plot, tooltip, area, keys, width){
        stacked_area_plot.append("path")
            .attr("class", "area")
            .attr("d", function(d) { return area(d.values); })
            .style("fill", function(d) { return keys(d.name); })
//            .on("mouseout", function() { tooltip.style("display", "none"); })
//            .on("mousedown", function(d) {
//                var xPosition = d3.mouse(this)[0],
//                    yPosition = d3.mouse(this)[1];
//
//
//                tooltip.attr("transform", "translate(" + xPosition + "," + yPosition + ")")
//                    .style({"display": "block"})
//                    .attr("fill",function() { return keys(d.name); });
//                tooltip.select("text")
//                    .text(function(){
//
//                        // printing date value
//
//                        var offsetFactor = width*0.8/ d.values.length;
//                        console.log(d.values[Math.floor(xPosition/offsetFactor)].timeStamp);
//                        return d.values[Math.floor(xPosition/offsetFactor)].timeStamp;
//                    });
//            });
        ;

    }

    /**
     * Makes a histogram with given data_in
     * @param data_in - the raw data object we want plotted
     * @param div - the name of the div element that we want to attach plot to
     * @param label - plot title
     * @param height - heigh of div
     * @param width - width of div
     */
    data.make_histogram = function(data_in,div,label, height, width){


        var plot_type = data_in.plot_type;
        // format of time stamp in data
        var format = d3.time.format("%Y-%m-%d %X %L");

        // A formatter for counts.
        var formatCount = d3.format(",.0f");

        var data_to_plotted ;
        if(data_in.plot_type == "histogram"){
            // the data we are plotting
            data_to_be_plotted = format_data_for_histogram(data_in);
        }
        else{
            // this will change
            data_to_be_plotted = data_in.data.t;

        }

        // specify number of bins
//        var num_bins = Math.round(Math.log2(data_to_be_plotted.length)); ( old one, which was wrong)
        var num_bins = 2*Math.round(Math.sqrt(data_to_be_plotted.length));

        // max number of bins so rectangular bars can be viewed ( 100 seemed skinny enough)
        if(num_bins > 100){

            num_bins = 100;
        }

//        console.log("num_bins ="+num_bins +" ,number of data points = "+data_to_be_plotted.length);

        // var margin = {top: 50, right: 0.1*width, bottom: 140, left: 0.1*width};
        var margin = {top: 0.1*height, right: 0.01*width, bottom: 30, left: 0.125*width};
        width = width - margin.left - margin.right;
        height = height - margin.top - margin.bottom;

        // setting up x axis domain and range
        var x = make_x_scale(data_in, width, data_to_be_plotted);

        // Generate a histogram using "num_bins" uniformly-spaced bins.
        var histogram_layout = generate_histogram_layout(num_bins, format, data_to_be_plotted, plot_type,x);

        // setting up y axis domain and range
        var y = make_y_scale(false, height, plot_type, histogram_layout);

        // physical appearance of x Axis
        var xAxis = make_x_axis(x,plot_type,width, num_bins);

        var yAxis = make_y_axis(y, false, height, plot_type);

        // the svg element we attach bars to
        draw_time_histogram(div, width, height, margin, label, histogram_layout, data_in,  x, y, xAxis, yAxis, formatCount);
    }

    /**
     * Makes a multi line plot  with given data_in
     * @param data_in - the raw data object we want plotted
     * @param div - the name of the div element that we want to attach plot to
     * @param label - plot title
     * @param height - heigh of div
     * @param width - width of div
     * @param show - points or not
     */
    data.make_multi_line_chart = function(data_in,div,label,height,width){

        var raw_data = data_in;

        render_plot(raw_data, false, height, width);

        function render_plot(raw_data, is_log,height, width) {

            var drawData = function(raw_data, xAxisLabel, yAxisLabel){

                var margin = {top: 0.1*height, right: 0.02*width, bottom: 10, left: 0.15*width}

                var div_height = height;
                var div_width  = width;

                width = width - margin.left - margin.right;
                height = height - margin.top - margin.bottom;

                var x = make_x_scale(raw_data,width);

                var y = make_y_scale(is_log, height);

                var xAxis = make_x_axis(x,raw_data.plot_type, width);

                var yAxis = make_y_axis(y, is_log, height, raw_data.plot_type);

                var line = line_function(x, y);

                var svg = create_svg(div,width,height,margin,label,"svg_multi_line_plot");

                var keys = keys_for_multiline_data(raw_data);

                var linlog  = range_and_domain_for_linlog_buttons();

                var data_to_be_plotted = fomat_data_for_multiline_plot(raw_data);

                set_y_domain(raw_data, is_log, y);

                draw_Axes(svg, yAxis, xAxis, width, height, yAxisLabel, xAxisLabel);

                // tick lines for x axis
                d3.select("#"+div).select(".x").selectAll(".tickline").style({"opacity": "0", "stroke-width": "0"});

                var tooltip = make_tooltip(svg);

                var types_of_plot = append_data_to_svg(svg,data_to_be_plotted, "multiline",x,y, keys, width, height, raw_data.plot_type);

                draw_lines("multiline", types_of_plot,line, tooltip, keys, width);

                make_legends(svg,keys,width,height);

                // make buttons for log and linear scales
                var logLinear = make_lin_log_button(svg, linlog, width, height);
                // defining functionality after click
                logLinear.on("click", function(e) {

                    d3.select("#"+div+"svg_multi_line_plot")
                        .remove();

                    var selectedLegend = d3.select(this).text();

                    previousSelected = selectedLegend;

                    if(selectedLegend == "log"){
                        render_plot(raw_data, true, div_height, div_width);
                    }
                    else if(selectedLegend == "linear"){
                        render_plot(raw_data, false, div_height, div_width);
                    }
                });

            };

            drawData(raw_data,raw_data.x_label,raw_data.y_label);
        };
    }

    /**
     * Makes a stacked area plot  with given data_in
     * @param data_in - the raw data object we want plotted
     * @param div - the name of the div element that we want to attach plot to
     * @param label - plot title
     * @param height - heigh of div
     * @param width - width of div
     */
    data.make_stacked_array_chart = function(data_in, div, label, height, width) {

        var drawData= function(raw_data,div, is_log, height, width){



            var margin = {top: 0.1*height, right: 0.01*width, bottom: 10, left: 0.15*width};

            var div_height = height;
            var div_width  = width;

            width = width - margin.left ;
            height = height - margin.top - margin.bottom;

            var x = make_x_scale(raw_data, width);

            var y = make_y_scale(is_log, height);

            var linlog  = range_and_domain_for_linlog_buttons();

            var xAxis = make_x_axis(x,raw_data.plot_type, width);

            var yAxis = make_y_axis(y, is_log, height, raw_data.plot_type);

            var line = area_chart_line(x,y);

            var area = area_chart_area(x,y);

            var stack = make_stack_layout(raw_data,is_log);

            var svg = create_svg(div, width, height, margin, label, "svg_area" );

            var keys = make_keys_for_stacked_area_chart(raw_data);

            var data_to_be_plotted = format_data_for_stacked_area_chart(raw_data, stack, is_log);

            set_y_domain(raw_data,is_log, y);

            make_legends(svg,keys,width,height);

            // make buttons for log and linear scales
            var logLinear = make_lin_log_button(svg, linlog, width, height);

            // defining functionality after click
            logLinear.on("click", function(e) {

                d3.select("#"+div+"svg_area")
                    .remove();

                var selectedLegend = d3.select(this).text();

                if(selectedLegend == "log"){
                    drawData(raw_data, div, true, div_height, div_width);
                }
                else{
                    drawData(raw_data, div, false, div_height, div_width);
                }

            });

            var tooltip = make_tooltip(svg);

            var stacked_area_plot = append_data_to_svg(svg, data_to_be_plotted, "stacked_area",x,y, keys,width,height, raw_data.plot_type, false);
            draw_area_for_stacked_area_plot(stacked_area_plot, tooltip, area, keys, width);

            draw_lines("stacked_area", stacked_area_plot,line);

            draw_Axes(svg,yAxis,xAxis,width,height,raw_data.y_label,raw_data.x_label);

        };

        var loadChart = function(raw_data,div, is_log, height, width){

            drawData(raw_data,div,is_log, height, width);

        };

        loadChart(data_in,div,false, height, width);

    }

    data.plot = function(dataSource,divIDName,label){


        // check if div exists
        var myElem = document.getElementById(divIDName);
        var height = myElem.offsetHeight;

        if (myElem == null) {
            myElem = document.createElement('div');
            myElem.id = divIDName;
            document.getElementsByTagName('body')[0].appendChild(myElem);

        }

        if(dataSource.data.length == 0){
            $('#'+divIDName).html("<p><b> No data available to be plotted </b></p>");
        }

        // remember to put myElem.offsetHeight back into the plot
        if( myElem.offsetHeight == 0){
            height = 400;
        }
        if(dataSource.plot_type == 'stacked_area_plot'){
            data.make_stacked_array_chart(dataSource,divIDName,label, height, myElem.offsetWidth);
        }
        else if(dataSource.plot_type == 'histogram' || dataSource.plot_type == 'histogram_real'){
            data.make_histogram(dataSource,divIDName,label, height, myElem.offsetWidth);
        }

        else if(dataSource.plot_type=='multi_line_plot'){
            data.make_multi_line_chart(dataSource,divIDName,label, height, myElem.offsetWidth);
        }
    }

    data.createDynamicTable = function(data, div_id) {
        // """
        // Requires data and a div id to to populate the data into a table dynamically.

        // Usage: ::\n        
        // Example input is:
        //     {'plot_type': 'columnar_table', 'meta': {'status': 'OK', 'code': 200}, 'data': [{'index': 0, 'target': {'target_id': 0, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 0, 'alt_description': 0}, 'rank': 0}, {'index': 2, 'target': {'target_id': 2, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 2, 'alt_description': 2}, 'rank': 1}, {'index': 3, 'target': {'target_id': 3, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 3, 'alt_description': 3}, 'rank': 2}, {'index': 4, 'target': {'target_id': 4, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 4, 'alt_description': 4}, 'rank': 3}, {'index': 6, 'target': {'target_id': 6, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 6, 'alt_description': 6}, 'rank': 4}, {'index': 5, 'target': {'target_id': 5, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 5, 'alt_description': 5}, 'rank': 5}, {'index': 1, 'target': {'target_id': 1, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 1, 'alt_description': 1}, 'rank': 6}, {'index': 8, 'target': {'target_id': 8, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 8, 'alt_description': 8}, 'rank': 7}, {'index': 9, 'target': {'target_id': 9, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 9, 'alt_description': 9}, 'rank': 8}, {'index': 7, 'target': {'target_id': 7, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 7, 'alt_description': 7}, 'rank': 9}]}
        // """

        console.log('got here');
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


    data.plotCurrentEmbedding = function(data, div_id) {
        /**
         * Generates an embedding of the triplet values.
         *
         * data should be a list of dictionaries of the form
         * {
         target: {
         primary_description: ,
         primary_type: ,
         },
         index: 
         x:
         y:
         }
         */
        d3TripletPlot = function(data) {
            console.log("in plot", data);

            if (data.length == 0){
                $('#'+div_id).html("<h3>No data available to be plotted.<h3>");
            }

            image_data = [];
            text_data = [];
            for(i=0; i < data.length; i++){
                if(data[i].target.primary_type=="image" || data[i].target.primary_type=="img"){
                    image_data.push(data[i]);
                } else if(data[i].target.primary_type=="text") {
                    text_data.push(data[i]);
                } else if(data[i].target.primary_type=="video") {
		    if(data[i].alt_type=='image'){
			image_data.push(data[i]);
		    } else {
			text_data.push(data[i]);
		    }
                }
            }

            console.log("image data", image_data);
            console.log("text data", text_data);

            var min_x = data[0].x;
            var max_x = data[0].x;

            var min_y = data[0].y;
            var max_y = data[0].y;

            // Could also potentially pass this in - should be sent from server
            for(i=0;i<data.length;i++){
                if(data[i].x<min_x){
                    min_x = data[i].x
                }
                if(data[i].x>max_x){
                    max_x = data[i].x
                }
                if(data[i].y<min_y){
                    min_y = data[i].y
                }
                if(data[i].y>max_y){
                    max_y = data[i].y
                }
            }


            var imagesize = 20 // relative size of images
            var dilation = 2 // how much do the images dialte when moused over
            var fontsize = 14 // size of text labels

            // size of viewport
            var height = 500;
            var width = 800;

            // scales to relate "real" coordinates with pixels
            var x = d3.scale.linear().domain([min_x,max_x]).range([0,width]),
                y = d3.scale.linear().domain([min_y,max_y]).range([0,height])

            // set zoom objects up with limits
            var zm = d3.behavior.zoom().scaleExtent([.7, 8]).on("zoom", zoom);

            var svg = d3.select("#"+div_id)
                .append("svg:svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .call(zm)
                .append("g");


            // this is for zooming (I think)
            svg.append("rect")
                .attr("class", "overlay")
                .attr("width", width)
                .attr("height", height)


            // add the tooltip area to the webpage
            var tooltip = d3.select("#"+div_id).append("div")
                .attr("class", "tooltip")
                .style("opacity", 0);


            // add some text spots
            d3.select("#"+div_id).append("p").text("    Click or hover over a target for more info. Pan/zoom with your mouse/trackpad");


            // add closer inspection of target div
            inspect_div = d3.select("#"+div_id).append("div")

            var imgs = svg.selectAll("image").data(image_data);
            imgs.enter()
                .append("svg:image")
                .attr("xlink:href", function(d) { return d.target.primary_description })
                .attr("x", function(d) { return x(d.x)-imagesize })
                .attr("y", function(d) { return y(d.y)-imagesize })
                .attr("width", function(d) { return 2*imagesize })
                .attr("height", function(d) { return 2*imagesize })
                .attr("stroke-width", "none")
                .attr("fill-opacity", .5)
                .on("mouseover", dilate )
                .on("mouseout", undilate )
                .on("mousedown", inspect_target );


             var texts = svg.selectAll("text").data(text_data);
            texts.enter()
                .append("svg:text")
                .attr("text", function(d) { return d.target.primary_description })
                .attr("x", function(d) { return x(d.x) })
                .attr("y", function(d) { return y(d.y) })
                .attr("font-family", "sans-serif")
                .attr("font-size", fontsize+"px")
                .attr("fill", "black")
                .attr("text-anchor", "middle")
                .attr("dominant-baseline","middle")
                .text( function(d) { console.log("text", d.x, d.y, d.target.primary_description); return d.target.primary_description } )
                .on("mouseover", function(d){ d3.select(this)
                    .attr("font-size", .75*dilation/zm.scale()*fontsize+"px")
                    .each( show_tooltip )
                } )
                .on("mouseout", function(d){ d3.select(this)
                    .attr("font-size", 1/zm.scale()*fontsize+"px")
                    .each( hide_tooltip )
                } )
                .on("mousedown", inspect_target );




            function zoom() {
                svg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");

                imgs.attr("x", function(d) { return x(d.x)-1/zm.scale()*imagesize })
                    .attr("y", function(d) { return y(d.y)-1/zm.scale()*imagesize })
                    .attr("width", function(d) { return 2*1/zm.scale()*imagesize })
                    .attr("height", function(d) { return 2*1/zm.scale()*imagesize })

                texts.attr("font-size", Math.round(fontsize/zm.scale())+"px")
            };

            function dilate(){
                d3.select(this)
                    .transition()
                    .delay(0)
                    .duration(10)
                    .attr("x", function(d) { return x(d.x)-dilation/zm.scale()*imagesize })
                    .attr("y", function(d) { return y(d.y)-dilation/zm.scale()*imagesize })
                    .attr("width", function(d) { return 2*dilation/zm.scale()*imagesize })
                    .attr("height", function(d) { return 2*dilation/zm.scale()*imagesize })
                    .each( show_tooltip )
            };


            function undilate(){
                d3.select(this)
                    .transition()
                    .duration(10)
                    .attr("x", function(d) { return x(d.x)-1/zm.scale()*imagesize })
                    .attr("y", function(d) { return y(d.y)-1/zm.scale()*imagesize })
                    .attr("width", function(d) { return 2/zm.scale()*imagesize })
                    .attr("height", function(d) { return 2/zm.scale()*imagesize })
                    .each( hide_tooltip )
            };

            function show_tooltip(){
                d3.select(this)
                    .each( function(d) { tooltip.transition()
                        .duration(200)
                        .style("opacity", .9);
                        tooltip.html(
                                "<div style=\"width:" + Math.round( Math.max(180,d.display.length*8) ) + "px\"><div style=\"text-align:right;background-color:#006699;height:60px;width:50px;float:left;\"><font color=#CCFFFF>"+
                                "<b>id</b>  <br>"+
                                "<b>name</b> <br>" +
                                "<b>x, y</b>  <br>"+
                                "</font></div>"+
                                "<div style=\"text-align:left;background-color:#EEEEEE;height:60px;width:" + Math.round( Math.max(180,d.display.length*8)-50) + "px;float:left;\">"+
                                " &nbsp;"+d.external_id + "<br>" +
                                " &nbsp;"+d.display + "<br>" +
                                " &nbsp;" + d.x.toFixed(4) + ", " + d.y.toFixed(4) + "</div></div>")
                            .style("left", (d3.event.pageX + 20) + "px")
                            .style("top", (d3.event.pageY - 28) + "px");
                    })
            }

            function hide_tooltip(){
                d3.select(this)
                    .each( function(d) { tooltip.transition()
                        .duration(300)
                        .style("opacity", 0);
                    })
            }

            function inspect_target(){
                d3.select(this)
                    .each( function(d) { inspect_div.html(
                            "<div style=\"width:" + Math.round( Math.max(180,d.display.length*8) ) + "px\"><div style=\"text-align:right;background-color:#006699;height:60px;width:50px;float:left;\"><font color=#CCFFFF>"+
                            "<b>id</b>  <br>"+
                            "<b>name</b> <br>" +
                            "<b>x, y</b>  <br>"+
                            "</font></div>"+
                            "<div style=\"text-align:left;background-color:#EEEEEE;height:60px;width:" + Math.round( Math.max(180,d.display.length*8)-50) + "px;float:left;\">"+
                            " &nbsp;"+d.external_id + "<br>" +
                            " &nbsp;"+d.display + "<br>" +
                            " &nbsp;" + d.x.toFixed(4) + ", " + d.y.toFixed(4) + "</div></div>");
                    })
            }
        }

        d3TripletPlot(data)
    }


}) (this.charts = {});
