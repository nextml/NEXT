
get_hidden_site_key = function(site_id){
    console.log(JSON.stringify({site_id:site_id}));
    $.ajax({
	type:"POST",
	url:"/get_hidden_site_key",
	data:JSON.stringify({site_id: site_id}),
	contentType:"application/json",
	success: function(data) {$( "#"+site_id ).html( data );}
	});
};

delete_site = function(site_id){
    console.log("delete"+JSON.stringify({site_id:site_id}));
    $.ajax({
	type:"POST",
	url:"/delete_site",
	data:JSON.stringify({site_id: site_id}),
	contentType:"application/json",
	success: function(data) {location.reload()}
	});
};



  
