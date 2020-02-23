$("#deactivator").on('submit', function () {
	event.preventDefault();
	var mip = $("#mip").val();
	var ip = $("#uplink").val();
	var comment = $("#comment").val();
	console.log(ip)
	$("#submit").prop("disabled", true);
	$("#submit").html(`<span id="submit-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Loading...`);
	$.ajax("/activator/get_acds_id_deactivator/", {
		method: "GET",
		data: {mip: mip, ip: ip, comment: comment}, 
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
			$("#acds_id").html(data['id']);
			$("#submit").prop("disabled", false);
			$("#submit").html('Send');
		}
	})
});

$("#device_move").on('submit', function () {
	event.preventDefault();
	var ip = $("#uplink").val();
	var comment = $("#comment").val();
	// console.log(ip)
	// console.log(comment)
	$("#submit").prop("disabled", true);
	$("#submit").html(`<span id="submit-spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>Loading...`);
	$.ajax("/activator/get_device_move/", {
		method: "GET",
		data: {ip: ip, comment: comment}, 
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
			$("#acds_id").html(data['id']);
			$("#submit").prop("disabled", false);
			$("#submit").html('Send');
		}
	})
});