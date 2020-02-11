$("#wbs_commit").on('submit', function () {
	event.preventDefault();
	var ip_address = $("#ip_address").val();
	var wlan0_ssid = $("#wlan0_ssid").val();
	var wlan0_azimuth = $("#wlan0_azimuth").val();
	var wlan0_mac = $("#wlan0_mac").val();
	var wlan1_ssid = $("#wlan1_ssid").val();
	var wlan1_azimuth = $("#wlan1_azimuth").val();
	var wlan1_mac = $("#wlan1_mac").val();
	var wlan2_ssid = $("#wlan2_ssid").val();
	var wlan2_azimuth = $("#wlan2_azimuth").val();
	var wlan2_mac = $("#wlan2_mac").val();

	$.ajax("set_wbs_data/", {
		method: "GET",
		data: {ip_address: ip_address, wlan0_ssid: wlan0_ssid, wlan0_azimuth: wlan0_azimuth, wlan0_mac: wlan0_mac, wlan1_ssid: wlan1_ssid, wlan1_azimuth: wlan1_azimuth, wlan1_mac: wlan1_mac, wlan2_ssid: wlan2_ssid,wlan2_azimuth:wlan2_azimuth, wlan2_mac:wlan2_mac}, 
		cache: false,
		fail: function(){alert("Что-то пошло не так");},
		success: function(data) {
			// data = JSON.parse(data);
			$('.form-control').val("");
			if ('error' in data) {
				document.getElementById('wbs_submit').setAttribute('style', 'color: red');
				function nothing(){
					document.getElementById('wbs_submit').setAttribute('style', 'color: wight');
					}
				setTimeout(nothing,1500);
				
				}
			if ( data['update'] == "Ok") {
				
				document.getElementById('wbs_submit').setAttribute('style', 'color: green');
				function wait5(){
					window.location.reload(true);
				}
				setTimeout(wait5,1000);
			}
		}
	})
});
