var colorsChart = [["#31a354"],["#3182bd"],["#756bb1"],["#636363"],["#c70076"],["#45bdbd"],["#"],["#"]];

var buttonsChart = [["#A9A9C6"]];

(function(data) {

    data.createDynamicTable = function(data, div_id) {
        // """
        // Requires data and a div id to to populate the data into a table dynamically.

        // Usage: ::\n        
        // Example input is:
        //     {'plot_type': 'columnar_table', 'meta': {'status': 'OK', 'code': 200}, 'data': [{'index': 0, 'target': {'target_id': 0, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 0, 'alt_description': 0}, 'rank': 0}, {'index': 2, 'target': {'target_id': 2, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 2, 'alt_description': 2}, 'rank': 1}, {'index': 3, 'target': {'target_id': 3, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 3, 'alt_description': 3}, 'rank': 2}, {'index': 4, 'target': {'target_id': 4, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 4, 'alt_description': 4}, 'rank': 3}, {'index': 6, 'target': {'target_id': 6, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 6, 'alt_description': 6}, 'rank': 4}, {'index': 5, 'target': {'target_id': 5, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 5, 'alt_description': 5}, 'rank': 5}, {'index': 1, 'target': {'target_id': 1, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 1, 'alt_description': 1}, 'rank': 6}, {'index': 8, 'target': {'target_id': 8, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 8, 'alt_description': 8}, 'rank': 7}, {'index': 9, 'target': {'target_id': 9, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 9, 'alt_description': 9}, 'rank': 8}, {'index': 7, 'target': {'target_id': 7, 'alt_type': 'text', 'primary_type': 'text', 'primary_description': 7, 'alt_description': 7}, 'rank': 9}]}
        // """

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
	    var rows = [];
	    for (var i = 0; i < data.data.length; i++) {
		var curr_row = [];
		for (var j=0; j<data.headers.length; j++){
                    if (data.headers[j].field == 'index' && data.data[i]['target']){
                        target = data.data[i].target;		
			if(target.primary_type == 'image'){
                            var img_col = '<td>'+'<img src='+target.primary_description+' style="max-height:100px;width:auto;"></img>';
			    curr_row[j] = img_col;
                        } else{
			    curr_row[j] = '<td>'+target.primary_description+'</td>';
                        }
		    } else{
			curr_row[j] = '<td>'+data.data[i][data.headers[j].field]+'</td>';
                    }
                }
		rows[i] = "<tr>" + curr_row.join(' ') + "</tr>";
	    }
	    body.html(rows.join(''))
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
		    data[i].target.primary_description = data[i].target.alt_description;
		    if(data[i].target.alt_type=="image"){
			image_data.push(data[i]);
		    } else {
			text_data.push(data[i]);
		    }
                }
            }

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
                .text( function(d) { return d.target.primary_description } )
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
