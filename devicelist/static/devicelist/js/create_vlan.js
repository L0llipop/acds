function get_create_vlan() {
	let ip_address = $('#ip_address').val();
	ip_address = ip_address.replace(/\,/g,'.');
	$('#ip_address').val(ip_address);

	let all_data = {
			'ip': ip_address,
			'vlan': $('#vlan').val()
		};

	let json_data = JSON.stringify(all_data)
	console.log('json_data: '+json_data);

	$.ajax("get_create_vlan/", {
		method: "GET",
		data: {all_data: json_data},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			// let res = JSON.parse(data)
			console.log(data);
			console.log('data: '+data['status']);
			console.log('data: '+data[1]);
			console.log('data: '+data[1]['ip']);
		}
	});
}

$('#create_vlan_submit').on('click', function(){
	get_create_vlan();
});