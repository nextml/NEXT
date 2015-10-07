/*next-widget.js - A javascript library to download widgets from the next_frontend_base service.

  Last Date Modified: Feb 8, 2015
  Authors: Lalit Jain, Nick Glattard
*/

var next_widget = (function($){
    var _url = "localhost";
    var _args = null;
    var _callbacks = null;
    
    return {	
	setUrl : function(url) {
	    _url = url;
	},
	
	getWidget : function(args,callbacks){
	    /**
  	     * Get a widget from next_frontend_base.
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
		//$('#'+div_id).html(data.html);

		// Build args dictionary for the processAnswer call
		// _args = {};
		// _args["app_id"] = args["app_id"];
		// _args["exp_uid"] = args["exp_uid"];
		// _args["widget_key"] = args["widget_key"];
		// _args["args"] = {};
		// console.log(data);
		//console.log(_args);
		//_args["args"]["query_uid"] = data.args["query_uid"]; // 
		// Set the callbacks
		//_callbacks = callbacks;
		//_callbacks.getQuery_success();
		console.log(data.json);
		callbacks(data)
	    }).fail( function(error){
		//callbacks.getQuery_failure();
		console.log("Failed to get widget data", error);
	    });
	},

	// getStats : function(args, response){
	//     // request("getstats", args, response);
	//     $.ajax({
	// 	type : "POST",
	// 	url : _url+"/api/experiment/stats",
	// 	data : JSON.stringify(args),
	// 	contentType: "application/json",
	// 	dataType: "json",
	// 	crossDomain: true
	//     }).done( function(data) {
	// 	console.log("inner data",data);   
	// 	response(data);
	//     }).fail(function(error){
	// 	console.log("Error in communicating with next_backend",jqXHR, textStatus, errorThrown);
	//     });
	// },



	processAnswer: function(target_id) {
	    /**
	     * Function for reporting an answer coming from a getQuery call.
	     * Is routed through the widget system.
	     * Input: target_id of the winner
	     */
	    _args["name"] = "processAnswer";
	    _args["args"]["target_winner"] = target_id;
	    console.log(_args)
	    $.ajax({
		url: _url+"/widgets/getwidget",
		type: "POST",
		contentType: "application/json",
		data: JSON.stringify(_args)
	    }).done( function(data, textStatus,XHR){
		_callbacks.processAnswer_success();
	    } ).fail(function(error){
		_callbacks.processAnswer_failure();
	    });
	}
    };

    

})(jQuery,d3);
