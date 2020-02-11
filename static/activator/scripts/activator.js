function delay(fn, ms) {
  let timer = 0
  return function(...args) {
	clearTimeout(timer)
	timer = setTimeout(fn.bind(this, ...args), ms || 0)
  }
}


$( "#model" ).autocomplete({
	delay:300,
	minLength:3,
	source: function( request, response ) {
		$.ajax("get_model/", {
			method: "GET",
			data: {model: request.term},
			cache: false,
			fail: function(){alert("fail");},
			error: function (xhr, ajaxOptions, thrownError) {
				alert(`${xhr.status} - ${thrownError}`);
			},
			success: function(data) {
				// $("#alert_model").removeClass('show');
				response($.map(data, function (value, key) {
					console.log(key,':', value);
					return {
						// name: key,
						// label: value,
						value: value
					};
				}));
				// response( data );
			}
		});
	},
	change: function (event, ui) {
		if (!ui.item) {
			this.value = '';
			$("#alert_model").addClass('show');
			$("#submit").prop("disabled", true);
			$("span.bdg_model").remove();
			$("div.block_model").append("<span class='badge badge-danger bdg_model'>error</span>");
		}

	},
	select: function (event, ui) {
 		selected = ui.item.label;
 		console.log(selected);
 		if (selected == 'DSL IES-1000') {
 			// Чтобы не вводили модель 1000
			$("#alert_model_zyxel").addClass('show');
			$("span.bdg_model").remove();
			$("#submit").prop("disabled", true);
			$("div.block_model").append("<span class='badge badge-danger bdg_model'>error</span>");
			return;
 		}
		$("#alert_model").removeClass('show');
		$("#alert_model_zyxel").removeClass('show');
		$("#submit").prop("disabled", false);
		$("span.bdg_model").remove();
		$("div.block_model").append("<span class='badge badge-success bdg_model'>ok</span>");
	}
});


function form_uplink() {
	var uplink = $("#uplink").val();
	$.ajax("/activator/get_uplink_info/", {
		method: "GET",
		data: {address: uplink},
		cache: false,
		fail: function(){alert("fail");},
		success: function(data){
			$('#address').html(' ');
			$.each(data, function(key, value){
				// console.log(data);
				if (key == 'error') {
					$("#uplink").focus();
					$("span.bdg_uplink").remove();
					$("div.block_uplink").append("<span class='badge badge-danger bdg_uplink'>error</span>");
					$("#alert_uplink").addClass('show');
					$("#submit").prop("disabled", true);
					// alert(value);
				}
				else if (key == 'ip') {
					// console.log(value);
					$('#uplink').val(value);
					uplink_value = $('#uplink').val();
					// $("#uplink").removeClass('text-danger');
					// $("#uplink").addClass('text-success');
					$("span.bdg_uplink").remove();
					$("div.block_uplink").append("<span class='badge badge-success bdg_uplink'>ok</span>");
					$("#alert_uplink").removeClass('show');
					$("#submit").prop("disabled", false);
				}
			});
		}
	});
};

$( "#uplink" ).keyup(delay(function() {
	length = $( "#uplink" ).val().length;
	if (length > 9) {
		form_uplink();
	}
	// alert( "Handler for .keyup() called." );
}, 500));

$( "#uplink" ).blur(function() {
	// length = $( "#uplink" ).val().length;
	form_uplink();
	// alert( "Handler for .keyup() called." );
});

$("#activator").on('submit', function () {
	event.preventDefault();
	$('#block_acds_data_textarea').remove();
	var mip = $("#mip").val();
	var uplink = $("#uplink").val();
	var address = $("#address").val();
	var model = $("#model").val();
	var serial = $("#serial").val();
	var sd = $("#sd").val();
	var office = $("#office").val();
	var old_ip = $("#old_ip").val();
	$("#submit").prop("disabled", true);
	$("#submit").html(`<span id="submit-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Loading...`);
	$.ajax("get_acds_id/", {
		method: "GET",
		data: {mip: mip, uplink: uplink, address: address, model: model, serial: serial, sd: sd, office: office, oldip: old_ip}, 
		cache: false,
		fail: function(){alert("fail");},
		error: function (xhr, ajaxOptions, thrownError) {
			// alert(`${xhr.status} - ${thrownError}`);
			alert ("Critical error")
			$("#submit").html('Send');
			$("#submit").prop("disabled", false);
		},
		success: function(data) {
			// data = JSON.parse(data);
			$('.form-control').val("");
			// console.log(data['acds_data']);
			if ('error' in data) {
				$("div.block_acds_data").append('<textarea id="block_acds_data_textarea" class="form-control col-6" rows="15" readonly></textarea>');
				$("#block_acds_data_textarea").append(`${data['error']}\n`);
			}
			if ('acds_data' in data) {	
				// $.each(data['acds_data'], function(key, value) {
				// 	$("#acds_data").append(`${key}: ${value}<br>`);
				// });
				$("div.block_acds_data").append('<textarea id="block_acds_data_textarea" class="form-control col-6" rows="15" readonly></textarea>');
				$("#block_acds_data_textarea").append(`IP - ${data['acds_data']['ipaddmgm']}\n`);
				$("#block_acds_data_textarea").append(`HOSTNAME - ${data['acds_data']['networkname']}\n`);
				$("#block_acds_data_textarea").append(`GW - ${data['acds_data']['gw']}\n`);
				$("#block_acds_data_textarea").append(`MASK - ${data['acds_data']['mask']}\n`);
				$("#block_acds_data_textarea").append(`NETWORK - ${data['acds_data']['network']}\n`);
				$("#block_acds_data_textarea").append(`MGMVLAN - ${data['acds_data']['mgmvlan']}\n`);
				// $("#block_acds_data_textarea").append(`vlans - ${data['acds_data']['vlans']}\n`);
				$("#block_acds_data_textarea").append(`hsi - ${data['acds_data']['hsi']}\n`);
				$("#block_acds_data_textarea").append(`iptv - ${data['acds_data']['iptv']}\n`);
				$("#block_acds_data_textarea").append(`ims - ${data['acds_data']['ims']}\n`);
				$("#block_acds_data_textarea").append(`tr069 - ${data['acds_data']['tr069']}\n`);
				$("#block_acds_data_textarea").append(`serial - ${data['acds_data']['serial']}\n`);
				$("#block_acds_data_textarea").append(`office - ${data['acds_data']['office']}\n`);
				// $("#block_acds_data_textarea").append(`port_uplink - ${data['acds_data']['port_uplink']}\n`);
				$("#block_acds_data_textarea").append(`ticket - ${data['acds_data']['ticket']}\n`);
				$("#block_acds_data_textarea").append(`model - ${data['acds_data']['model']}\n`);
			}
			$("#acds_id").html(data['id']);
			$("#submit").prop("disabled", false);
			$("#submit").html('Send');
		}
	})
});

$("#address").suggestions({
	token: "4050395393551c7931ceabf9015365c473c8879b",
	type: "ADDRESS",
	deferRequestBy: 300,
	minChars: 4,
	constraints: {
	  label: "",
	  // ограничиваем поиск по коду ФИАС
	  locations: [
			{"region_fias_id": "54049357-326d-4b8f-b224-3c6dc25d6dd3"}, //Tyumen
			{"region_fias_id": "4a3d970f-520e-46b9-b16c-50d4ca7535a8"}, //Kurgan
			{"region_fias_id": "d66e5325-3a25-4d29-ba86-4ca351d9704b"}, //HMAO
			{"region_fias_id": "27eb7c10-a234-44da-a59c-8b1f864966de"}, //CHEL
			// {"region_fias_id": "краснодарский"},
			// {"region_fias_id": "ростовская"}
		],
		// deletable: true
	},
	/* Вызывается, когда пользователь выбирает одну из подсказок */
	onSelect: function(suggestion) {
		fias_data = suggestion['data']['house_fias_id'];
		console.log(suggestion['data']);
		if (!fias_data) {
			$("#alert_address").addClass('show');
			$("#submit").prop("disabled", true);
			$("span.bdg_address").remove();
			$("div.block_address").append("<span class='badge badge-danger bdg_address'>error</span>");
		}
		else {
			$("#alert_address").removeClass('show');
			$("#submit").prop("disabled", false);
			$("span.bdg_address").remove();
			$("div.block_address").append("<span class='badge badge-success bdg_address'>ok</span>");
		}

	}
});

$( "#address" ).blur(function() {
	address_status = $(".bdg_address").html();
	if (!address_status || address_status == 'error') {
		console.log(`status - ${address_status}`)
		$("#alert_address").addClass('show');
		$("#submit").prop("disabled", true);
	}
	else if (address_status == 'ok') {
		$("#alert_address").removeClass('show');
		$("#submit").prop("disabled", false);		
	}
});


$("#submit_test").on('click', function () {
	$('#block_acds_data_textarea').remove();
	test = {"aa":"bb","cc":"dd","c1":"dd","c2":"dd","c3":"dd"}
	// test = JSON.parse(test);
	event.preventDefault();
	// alert(test);
	// $("div.block_acds_data").append('<textarea id="block_acds_data_textarea" class="form-control col-6" rows="10" readonly></textarea>');
	// $("#buttons").append('<button class="btn btn-primary delegete" id="delegete" type="button" value="delegete">delegete</button>')
	$.each(test, function(key, value) {
		$("#block_acds_data_textarea").append(value+'\n');
		console.log(value);
	});
});
