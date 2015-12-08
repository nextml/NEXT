/*
  next-widget.js - A javascript library to download widgets from the next service.
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

	getStats : function(args, callbacks){
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

	processAnswer: function(args, query_meta) {
	    _args["name"] = "processAnswer";
	    $.extend(_args["args"], args);
	    currTime = new Date().getTime();
	    _args["args"]["response_time"] = (currTime -  _queryTime)/1000.;
	    
	    console.log(_args);
	    if (typeof query_meta !== "undefined") {
		_args["args"]["query_meta"] = query_meta;
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
	    while (0 !== currentIndex) {
		randomIndex = Math.floor(Math.random() * currentIndex);
		currentIndex -= 1;
		temporaryValue = array[currentIndex];
		array[currentIndex] = array[randomIndex];
		array[randomIndex] = temporaryValue;
	    }
	    return array;
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
	
	makeRandomString : function(length){
	    var text = "";
	    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
	    for( var i=0; i < length; i++ ){
		text += possible.charAt(Math.floor(Math.random() * possible.length));
	    }
	    return text;
	}
    };
})(jQuery);
