function get_generator() {
  let model = $('#models').val();
  let ip = $('#ip').val();
  ip = ip.replace(/\,/g,'.');
  $('#ip').val(ip);
  let mask = $('#mask').val();
  let gateway = $('#gateway').val();
  let hostname = $('#hostname').val();
  let uplink_hostname = $('#uplink_hostname').val();
  let uplink_port = $('#uplink_port').val();
  let MGM = $('#MGM').val();
  let HSI = $('#HSI').val();
  let IPTV = $('#IPTV').val();
  let IMS = $('#IMS').val();
  let TR069 = $('#TR069').val();
  // alert(result);
  result = model + " " + ip + " " + mask + " " + gateway + " " + hostname + " " + uplink_hostname + " " + MGM + " " + HSI + " " + IPTV + " " + IMS + " " + TR069
  // $("#result").html(result);
  console.log(result);
  // document.getElementById('result').innerHTML = result;
  $.ajax("get_template/", {
    method: "GET",
    data: {model: model, ip: ip, mask: mask, gateway: gateway, hostname: hostname, uplink_hostname: uplink_hostname, uplink_port: uplink_port, MGM: MGM, HSI: HSI, IPTV: IPTV, IMS: IMS, TR069: TR069},
    // data: {model: model},
    cache: false,
    fail: function(){alert("fail");},
    success: function(data){
      // data = JSON.parse(data);
      console.log(data);
      // $("#result").html(result + "test");
      var user = "None";
      if (data['error']){
        alert(`Error: ${data['error']}`);
      }
      else{
        if (data['user']){
          user = data['user']
        }
        $('#setting_all').empty();
        $('#setting_mng').empty();
        $('#setting_uplink').empty();
        $('#download_software').empty();
        for (var i in data['setting_all']) {
          $('#setting_all').append(data['setting_all'][i] + "\n");
        }
        for (var i in data['setting_mng']) {
          $('#setting_mng').append(data['setting_mng'][i] + "\n");
        }
        for (var i in data['setting_uplink']) {
          $('#setting_uplink').append(data['setting_uplink'][i] + "\n");
        }
        for (var i in data['download_software']) {
          $('#download_software').append(data['download_software'][i] + "\n");
        }
      }
    }
  });
}


$('#generator_submit').on('click', function(){
  get_generator();
  return false;
});

function get_data_device() {
  let ip = $('#ip').val();
  ip = ip.replace(/\,/g,'.');
  $('#ip').val(ip);
  console.log(`ip: ${ip}`);
  $.ajax("get_data_device/", {
    method: "GET",
    data: {ip: ip},
    cache: false,
    fail: function(){alert("fail");},
    success: function(data){
      console.log(`data: ${data}`);
      $('#mask').val(data['mask']);
      $('#gateway').val(data['gw']);
      $('#hostname').val(data['hostname']);
      $('#uplink_hostname').val(data['uplink']);
      $('#uplink_port').val(data['port_uplink']);
      $('#MGM').val(data['mng']);
      $('#HSI').val(data['hsi']);
      $('#IPTV').val(data['iptv']);
      $('#IMS').val(data['ims']);
      $('#TR069').val(data['tr069']);
      $(`#models option:contains("${data['model_select']}")`).prop('selected', true);
      // get_generator();
    }
  });
}


$('#get_data_device_submit').on('click', function(){
  get_data_device();
  return false;
});