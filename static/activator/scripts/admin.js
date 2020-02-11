 // var tf1 = setFilterGrid("tickets_table");

$('.btn-primary.getip').on('click', function(){
	let id = $(this).attr("value");
	let status = $(`#badge_${id}`).html();

	if (status == 'init' || status == 'ok') {
		alert('free_ip already finished')
		return
	}
	if (status == 'error(c)') {
		alert('free_ip already finished')
		return
	}
	console.log(`id: ${id} | status: ${status}`);
	$(`#getip_${id}`).html(`<span id="submit-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`);
	$.ajax("free_ip_refresh/", {
		method: "GET",
		data: {id: id, status: status},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			// data = JSON.parse(data);
			console.log(`data: ${JSON.stringify(data)} | status: ${data['status']}`);
			if (data['status'] == 'init') {
				// $(`#getip_${id}`).prop("disabled", true);
				$(`#getip_${id}`).html('getip');
				$(`#ip_${id}`).html(`<a target="_blank" href="http://10.180.7.34:8080/topology/topology.pl?ip=${data['ip']}&submit=Submit">${data['ip']}</a>`); 
				$(`#network_${id}`).html(`${data['network']}; ${data['mgmvlan']}`);
				$(`#hostname_${id}`).html(data['hostname']);
				$(`#vlans_${id}`).html(data['vlans']);
				$(`#address_${id}`).html(data['address']);
				// $(`#status.${id}`).html(`<span class="badge badge-${data['badge']}" title="${data['report']}" id="badge.${id}">${data['status']}</span>`);
			}
			else if (data['status'] == 'error(f)') {
				$(`#getip_${id}`).html('getip');
			}
			$(`#status_${id}`).html(`<span class="badge badge-${data['badge']}" title="${data['report']}" id="badge_${id}">${data['status']}</span>`);
			// if (data['status'] == 'error') {
			// }
			if (data['status'] == 'close') {
				// alert(id);
				$(`#tr_${id}`).remove();
			}
		}
	});
});

$('.config').on('click', function(){
	let id = $(this).prop("value");
	let status = $(`#badge_${id}`).html();
	let online = $(`#str_${id}`).attr("value");
	// let ip = $(`#ip_${id}`).html();
	// let model = $(`#model_${id}`).attr('value');
	// console.log(status);
	// console.log(online);
	// console.log(id);
	// console.log(model);
	// if (status == 'ok') {
	// 	$(`#str_${id}`).remove();
	// 	// return;
	// }
	if (status != 'init' && status != 'ok' && status != 'del' && status != 'error(c)' && status != 'other') {
		alert(`free_ip in status ${status}, it's not ok, must be "init"`)
		return;
	}
	if (online != 'success'  && online != 'warning' && online != 'info') {
		alert('device unreacheble');
		return;
	}
	$(`#config_${id}`).html(`<span id="submit-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`);
	$.ajax("device_configure/", {
		method: "GET",
		data: {id: id},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			if(data['report'] == 'configuring') {
				alert('configuring already started by another user')
				$(`#config_${id}`).html('config');
			}
			else if(data['report'] == 'not in argus') {
				$(`#str_${id}`).remove();
				alert('already configured, waiting argus');
			}
			else if(data['status'] == 'error(c)') {
				$(`#config_${id}`).html('config');
			}
			else if(data['status'] == 'finished') {
				$(`#str_${id}`).remove();
			}
			else if(data['status'] == 'ok') {
				$(`#str_${id}`).remove();
				// $(`#config_${id}`).html('close');
				// $(`#config_${id}`).removeClass('btn btn-primary');
				// $(`#config_${id}`).addClass('btn btn-danger');
			}
			$(`#status_${id}`).html(`<span class="badge badge-${data['badge']}" title="${data['report']}" id="badge_${id}">${data['status']}</span>`);
		}
	});
});

$('.btn-info.modalwin').on('click', function(){
	let today = new Date();
	let time = today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
	console.log(time);
	let id = $(this).prop("id");
	$('#select_templates').empty();
	$.ajax("get_ticket_info/", {
		method: "GET",
		data: {id: id},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			// console.log(data);
			$('#modal-add').html(data['office']);
			$('#modal-ser').html(data['serial']);
			$('#modal-rea').html(data['reason']);
			$('#modal-mail').html(data['email']);
			$('#modal-term').html(data['termination']);
			// $('#modal-comm').html(data['ticket']);
			$('#comment').val(data['ticket']);
			$('#ModalLabel').html(id);
			$.each(data['vlans'], function(key, value) {
				// console.log(key);
				// console.log(value['hsi']);
				$('#select_templates').append(`<div class="radio"><label class="my-0"><input id="${key}" type="radio" name="optradio" value="${key}">HSI - ${value['hsi']} IPTV - ${value['iptv']} IMS - ${value['ims']} TR - ${value['tr']} net - ${value['network']}</label></div>`);
			});
			$(`#${data['acsw_node_id']}`).attr('checked', true)
		}
	});
});

$('.insert_template').on('click', function(){
	let id = $('#ModalLabel').html();
	let acsw_node_id = ($("input:radio:checked").val())
	let comment = ($('#comment').val())
	console.log(id);
	console.log(acsw_node_id);
	console.log(comment);
	$.ajax("get_acsw_node_id_update/", {
		method: "GET",
		data: {id: id, acsw_node_id: acsw_node_id, comment: comment}, 
		cache: false,
		fail: function(){alert("fail");},
		error: function (xhr, ajaxOptions, thrownError) {
			// alert(`${xhr.status} - ${thrownError}`);
			alert ("Critical error AJAX insert_template");
		},
		success: function(data) {
			if (data['status'] == 'updated') {
				alert(data['message']);
				location.reload();
			}
		}
	});
});

$('.delete_ticket').on('click', function(){
	let id = $('#ModalLabel').html();
	// let ip = $(`#ip_${id}`).html();
	let status = $(`#badge_${id}`).html();
	// console.log(status);
	if (status != 'init' && status != 'ok' && status != 'new' && status != 'other' && status != 'error(f)' && status != 'error(c)') {
		alert("Удалить можно только заявку на ввод нового оборудования")
		return
	}
	$.ajax("get_acds_id_remove/", {
		method: "GET",
		data: {id: id}, 
		cache: false,
		fail: function(){alert("fail");},
		error: function (xhr, ajaxOptions, thrownError) {
			// alert(`${xhr.status} - ${thrownError}`);
			alert("Critical error AJAX delete_ticket");
		},
		success: function(data) {
			if (data['answer'] == 'deleted') {
				$(`#str_${id}`).remove();
			}
			else {
				alert("only in status ['new', 'init', 'other']")
			}
		}
	});
});

$('.argus').on('click', function(){
	let id = $(this).prop("value");
	// console.log(`delete ${id} ${ip}`);
	// alert(id);
	$.ajax("get_acds_argus_status/", {
		method: "GET",
		data: {id: id}, 
		cache: false,
		fail: function(){alert("fail");},
		error: function (xhr, ajaxOptions, thrownError) {
			// alert(`${xhr.status} - ${thrownError}`);
			alert ("Critical error AJAX argus_update");
		},
		success: function(data) {
			if (data['answer'] == 'ok') {
				$(`#str_${id}`).remove();
			}
		}
	});
});