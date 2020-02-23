// var date = new Date().toTimeString().replace(/.*(\d{2}:\d{2}:\d{2}).*/, "$1");
// $('#date').html(date);
document.querySelector('#room-name-input').focus();
document.querySelector('#room-name-input').onkeyup = function(e) {
	if (e.keyCode === 13) {  // enter, return
		document.querySelector('#room-name-submit').click();
	}
};

document.querySelector('#room-name-submit').onclick = function(e) {
	var roomName = document.querySelector('#room-name-input').value;
	window.location.pathname = '/chat/' + roomName + '/';
};


$('#log_free_ip').on('click', function(){
  window.location.pathname = '/chat/log_free_ip/';
});

$('#log_configure').on('click', function(){
  window.location.pathname = '/chat/log_configure/';
});
$('#mass_config').on('click', function(){
  window.location.pathname = '/chat/massconfig/';
});