/*
  next-widget.js - A javascript library to download widgets from the next_backend service.

  Last Date Modified: Feb 8, 2015
  Authors: Lalit Jain, Nick Glattard
*/

var next_widget = (function($){
    var _url = "localhost";
    var _args = null;
    var _callbacks = null;
    var _queryTime = 0;
    return {	
		setUrl : function(url) {
		    _url = url;
		},
		
		getQuery : function(div_id,args,callbacks){
		    /**
	  	     * Get a query widget from next_frontend_base.
		     * 
		     * Usage: 
	  	     * next-widget.getwidget(
		     *	div_id, 
		     * //args
	             *   	{
	  	     *		name: widget name,
		     *		app_id: application id,
		     *		exp_uid: experiment id
		     *		key: experiment key (needs to be migrated to widget key)
		     *		args: optional, application dependent args, can safely be empty
	  	     *	},

	  	     * //callbacks
	  	     *	{
	  	     *		success: callback on a successful widget load
	  	     *	}
		     * );
		     
		     ****************************************/
		    //console.log("args for widget",args);
		    $.ajax({
			url: _url+"/api/widgets/getwidget",
			type: "POST",
			contentType: "application/json",
			data: JSON.stringify(args),
			dataType: "json"
		    }).done( function(data,textStatus, jqXHR) {
				// Set the div to this html
				$('#'+div_id).html(data.html);
				_queryTime = new Date().getTime();
				
				// Build args dictionary for the processAnswer call
				_args = {};
				_args["exp_uid"] = args["exp_uid"];
				_args["widget_key"] = args["widget_key"];
				_args["args"] = {};
				_args["args"]["query_uid"] = data.args["query_uid"]; 
				
				// Set the callbacks
				_callbacks = callbacks;
				_callbacks.getQuery_success(data);

		    }).fail( function(error){
		    	console.log("Failed to get widget data", error);
				callbacks.widget_failure();
		    });
		},	

	    getQueryVars : function() {
			var query = window.location.search.substring(1);
			var vars = query.split('&');
			var pair = {};
			for (var i = 0; i < vars.length; i++) {
			    key_val = vars[i].split('='); 
			    pair[key_val[0]] = key_val[1];
			}
			return pair;
		},

		getStats : function(args, callbacks){
		    // request("getstats", args, response);
		    $.ajax({
			type : "POST",
			url : _url+"/api/widgets/getStats",
			data : JSON.stringify(args),
			contentType: "application/json",
			dataType: "json",
			crossDomain: true
		    }).done( function(data) {
				console.log("inner data",data); 
				callbacks.getStats_success()  
				response(data);
		    }).fail(function(error){
				console.log("Error in communicating with next_backend",jqXHR, textStatus, errorThrown);
				callbacks.getStats_failure();
		    });
		},

	processAnswer: function(target_id, query_meta) {
		    /**
		     * Function for reporting an answer coming from a getQuery call.
		     * Is routed through the widget system.
		     * Input: target_id of the winner
		     */
		    _args["name"] = "processAnswer";
		    _args["args"]["target_winner"] = target_id;
		    currTime = new Date().getTime();
		    _args["args"]["response_time"] = (currTime -  _queryTime)/1000.;
	    console.log(_args)
	    if (typeof meta !=== "undefined") {
		_args["args"]["query_meta"] = meta
	    }
		    $.ajax({
			url: _url+"/api/widgets/getwidget",
			type: "POST",
			contentType: "application/json",
			data: JSON.stringify(_args)
		    }).done( function(data, textStatus,XHR){
				_callbacks.processAnswer_success();
		    } ).fail(function(error){
		    	console.log("Error in communicating with next_backend",jqXHR, textStatus, errorThrown);
				_callbacks.widget_failure();
		    });
		},

		getInfo: function(args, callbacks) {
		    /**
		     * Function for getting instructions and debrief.
		     * Is routed through the widget system.
		     * Input: empty args dict
		     */
		    $.ajax({
			url: _url+"/api/widgets/getwidget",
			type: "POST",
			contentType: "application/json",
			data: JSON.stringify(args)
		    }).done( function(data, textStatus,XHR){
				console.log("getInfo success", data);
				callbacks.getInfo_success(data);
		    } ).fail(function(error){
		    	console.log("Error in communicating with next_backend");
			callbacks.widget_failure();
		    });
		},

	    	shuffle: function(array) {
	    	var currentIndex = array.length, temporaryValue, randomIndex ;
		
		// While there remain elements to shuffle...
		while (0 !== currentIndex) {
	      
		    // Pick a remaining element...
		    randomIndex = Math.floor(Math.random() * currentIndex);
		    currentIndex -= 1;
		    
		    // And swap it with the current element.
		    temporaryValue = array[currentIndex];
		    array[currentIndex] = array[randomIndex];
		    array[randomIndex] = temporaryValue;
		}

		return array;
	    },

	    makeRandomString : function(length)
		{
		    var text = "";
		    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
		    for( var i=0; i < length; i++ ){
			text += possible.charAt(Math.floor(Math.random() * possible.length));
		    }
		    return text;
		}
    };

    

})(jQuery,d3);
