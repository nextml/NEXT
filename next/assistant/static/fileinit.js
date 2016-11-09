var data = {'args':null,'targets':null};
var ready = false;

function file_read(form){
    var reader = new FileReader();
    reader.onload = function(e) {
	data[form] = e.target.result;
	ready = data['args'] != null && data['targets'] != null;
    };
    reader.readAsDataURL(new_file.files[0]);
}

function submit_form(){
    if(!ready){
	alert('still uploading');
	return;
    }
}

function submit_form(e){
    e.preventDefault();
    console.log(data);
    var XHR = new XMLHttpRequest();
    XHR.addEventListener("load", function(event) {
	self.submit_callback(event.target.responseText);
    });
    XHR.addEventListener("error", function(event) {
	console.log('Oops! Something went wrong.');
    });
    XHR.open("POST", self.target);
    XHR.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    XHR.send(JSON.stringify(data));
    return false;
}
