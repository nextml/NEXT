var data = {'args':null,'targets':null,"bucket_id":"","key_id":"","secret_key":""};
var ready = false;

var params = ["bucket_id","key_id","secret_key"];
var saved_params = ["bucket_id","key_id"];

function read_saved(){
    var all_cookies = document.cookie.split(';');
    for(var c = 0; c < all_cookies.length; c++){
	var cookie = all_cookies[c].split('=');
	var i = saved_params.indexOf(cookie[0].trim());
	if(i >= 0){
	    document.getElementById(saved_params[i]).value = cookie[1].trim();
	}
    }
}

function file_read(form){
    var reader = new FileReader();
    var set_onload = function(f){
	reader.onload = function(e) {
	    console.log('done with',f);
	    data[f] = e.target.result;
	};
	console.log('set onload',f);
    };
    set_onload(form);
    reader.readAsDataURL(document.getElementById(form).files[0]);
}

function serialise(data){
    ans = "";
    payload = "";
    for(var x in data){
	if(data[x] == null || data[x] == "") continue;
	ans += x + ":" + data[x].length + ";";
	payload += data[x]
    }
    ans = ans.slice(0,-1)+"\n"+payload;
    return ans;
}

function submit_form(){
    if(data['args'] == "" || data['args'] == null){
	alert('Please select an arguments file.');
	return;
    }
    for(var i = 0; i < params.length; i++){
	data[params[i]] = document.getElementById(params[i]).value.trim();
    }
    for(var i = 0; i < saved_params.length; i++){
	document.cookie = saved_params[i] + ' = ' + document.getElementById(saved_params[i]).value.trim() + '; ';
    }
    console.log(data);
    var XHR = new XMLHttpRequest();
    XHR.addEventListener("load", function(event) {
	console.log("DID IT",event.target.responseText);
	ret = JSON.parse(event.target.responseText);
	if(ret.success){
	    document.getElementById('exp_status').innerHTML = "Success!  <br /><a target=\"_blank\" href=\"/dashboard/experiment_dashboard/"+ret.exp_uid+"/"+ret.app_id+"\">Experiment dashboard</a><br /><a target=\"_blank\" href=\"/query/query_page/query_page/"+ret.exp_uid+"\">Experiment query page</a>";
	}
	else{
	    document.getElementById('exp_status').innerHTML = "There was an error:  <br /><pre style=\"color:red;\">"+ret.message+"</pre>";
	    document.getElementById('initExp').disabled = false;
	}
    });
    XHR.addEventListener("error", function(event) {
	document.getElementById('exp_status').innerHTML = "There was an unknown network error:";
	document.getElementById('initExp').disabled = false;
    });
    XHR.open("POST", target);
    XHR.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    document.getElementById('initExp').disabled = true;
    document.getElementById('exp_status').innerHTML = "Launching... (this may take a while, depending on the size of the targets)";
    XHR.send(serialise(data));
    return false;
}

window.onload = function(){
    console.log("Reading cookies");
    read_saved();
}
