$("#acds_id_btn").on('click', function () {
	event.preventDefault();
	let acds_id = $("#id").val();
	if (!acds_id) {
		alert("Введите ID заявки")
	}
	console.log(acds_id);
	$.ajax("/activator/get_history/", {
		method: "GET",
		data: {id: acds_id},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			if(data['report'] == 'error') {
				alert('истории не найдено');
				$('#logs').empty();
			}
			else if(data['report'] == 'ok') {
				$('#logs').html('<thead><tr><th class="text-center" scope="col" style="width: 10%">ip</th><th class="text-center" scope="col" style="width: 10%">user</th><th class="text-center" scope="col" style="width: 65%">message</th><th class="text-center" scope="col" style="width: 15%">time</th></tr></thead>');
				$('#logs').append('<tbody id="logs_table"></tbody>');
				// $('#logs_table').html('<tr><td>123123</td><td>123123</td><td>123123</td></tr>');
				for (var i = data['logs'].length - 1; i >= 0; i--) {
					$('#logs_table').append(`<tr><td>${data['logs'][i][1]}</td><td>${data['logs'][i][3]}</td><td>${data['logs'][i][4]}</td><td>${data['logs'][i][5]}</td></tr>`);
					// console.log(data['logs'][i][1])
				}
			}
		}
	});
});


