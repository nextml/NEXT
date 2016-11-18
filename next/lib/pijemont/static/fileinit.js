var data = {'args':null,'targets':null,"bucket_id":"","key_id":"","secret_key":""};
var ready = false;

var params = ["bucket_id","key_id","secret_key"];

function file_read(form){
    var reader = new FileReader();
    var set_onload = function(f){
	reader.onload = function(e) {
	    console.log('done with',f);
	    data[f] = e.target.result;
	    document.getElementById(f+'_status').innerHTML='Ready!';
	};
	console.log('set onload',f);
    };
    set_onload(form);
    document.getElementById(form+'_status').innerHTML='Loading...';
    reader.readAsDataURL(document.getElementById(form).files[0]);
}

function serialise(data){
    ans = "";
    payload = "";
    for(var x in data){
	ans += x + ":" + data[x].length + ";";
	payload += data[x]
    }
    ans = ans.slice(0,-1)+"\n"+payload;
    return ans;
}

function submit_form(){
    if(data['args'] == null){
	alert('Please select an arguments file.');
	return;
    }
    for(var i = 0; i < params.length; i++){
	data[params[i]] = document.getElementById(params[i]).value;
    }
    if(data['targets'] != null){
	for(var i = 0; i < params.length; i++){
	    if(data[params[i]].length == 0){
		alert("Please enter "+params[i]);
		return;
	    }
	}
    }
    console.log(data);
    var XHR = new XMLHttpRequest();
    XHR.addEventListener("load", function(event) {
	console.log("DID IT",event.target.responseText);
	ret = JSON.parse(event.target.responseText);
	if(ret.success){
	    document.getElementById('exp_status').innerHTML = "Success!  <br /><a href=\"/dashboard/experiment_dashboard/"+ret.exp_uid+"/"+app_id\">Experiment dashboard</a><br /><a href=\"/query/query_page/query_page/"+ret.exp_uid+"\">Experiment query page</a>";
	}
	else{
	    document.getElementById('exp_status').innerHTML = "There was an error:  <br /><font color=\"red\"><pre>"+ret.message+"</pre></font>";
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
    document.getElementById('exp_status').innerHTML = "Attempting to Launch...";
    XHR.send(serialise(data));
    return false;
}
