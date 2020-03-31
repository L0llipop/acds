let userName = $('#username').val();
console.log(`username: ${userName}`);

let chatSocket = new WebSocket(
	'ws://' + window.location.host +
	'/ws/vpn/' + userName + '/');
console.log(chatSocket)

chatSocket.onmessage = function (e) {
	let data = JSON.parse(e.data);
	// let data = e;
	data = JSON.parse(data['message']);
	console.log(data);
	console.log('===============', data['time'], '===============');
};

chatSocket.onopen = function (e) {
	console.log('Open websocket');
	$(`#topology_submit`).prop('disabled', false);
};

chatSocket.onclose = function (e) {
	console.error('Chat socket closed unexpectedly');
	$(`#topology_submit`).prop('disabled', true);
	$('#spinner').remove();
	alert("Необходимо обновить страницу");
};



$('#online').on('click', function () {
	let checked = $('#online').prop('checked');
	console.log(`checked: ${checked}`);
});
