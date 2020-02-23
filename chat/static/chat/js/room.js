let roomName = $("#room_name").val();
console.log(`roomName: ${roomName}`);

let chatSocket = new WebSocket(
	'ws://' + window.location.host +
	'/ws/chat/' + roomName + '/');

chatSocket.onmessage = function(e) {
	let data = JSON.parse(e.data);
	let message = data['message'];
	console.log(e);
	// let message = e.data['message'];
	let date = new Date().toTimeString().replace(/.*(\d{2}:\d{2}:\d{2}).*/, "$1");
	document.querySelector('#chat-log').value += (`${date} | ${message}\n`);
};

chatSocket.onclose = function(e) {
	console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function(e) {
	if (e.keyCode === 13) {  // enter, return
		document.querySelector('#chat-message-submit').click();
	}
};

document.querySelector('#chat-message-submit').onclick = function(e) {
	let messageInputDom = document.querySelector('#chat-message-input');
	let message = messageInputDom.value;
	chatSocket.send(JSON.stringify({
		'message': message
	}));

	messageInputDom.value = '';
};


$("#chat-log").change(function() {
	scrollToBottom();
});

function scrollToBottom() {
	$('#chat-log').scrollTop($('#chat-log')[0].scrollHeight);
}