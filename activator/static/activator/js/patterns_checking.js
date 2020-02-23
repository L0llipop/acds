function get_patterns() {
  let ip_address = $('#ip_address').val();
  // document.getElementById('result').innerHTML = ip_address;
  if (ip_address){
    console.log(`ip_address: ${ip_address}`);
    $.ajax("get_patterns/", {
      method: "GET",
      data: {ip_address: ip_address},
      cache: false,
      fail: function(){alert("fail");},
      success: function(data){
        console.log(data);
        // console.log(`len: ${Object.keys(data).length}`);
        if (Object.keys(data).length > 1){
          $('#all_data').empty();
          $('#DEVICE_ID').val(data[1]['DEVICEID']);

          let cheack_access = 0;
          // console.log(`data['group']: ${data['group'].indexOf('admins')} | ${typeof(data['group'])}`);
          if (data['group'].indexOf('admins') || data['group'].indexOf('engineers')){
            cheack_access = 1;
          }
          for (let pn in data) {
            if (isNaN(pn))continue;

            $('#all_data').append(`<div id="pn_${pn}">`);
            $(`#pn_${pn}`).append(`<table id="data_table_${pn}" class="table table-info table-sm my-0">`);
            $(`#data_table_${pn}`).append(`<tbody><tr id="data_device_${pn}">`);

            $(`#data_device_${pn}`).append(`<td class="text-left" id="DEVICEID">${data[pn]['DEVICEID']}`);
            $(`#data_device_${pn}`).append(`<td class="text-center">${data[pn]['IPADDMGM']}`);
            $(`#data_device_${pn}`).append(`<td class="text-center">${data[pn]['NETWORKNAME']}`);
            $(`#data_device_${pn}`).append(`<td class="text-right">${data[pn]['DEVICEMODELNAME']}`);

            $(`#pn_${pn}`).append(`<table id="data_table_vlan_${pn}" class="table table-sm my-0">`);
            $(`#data_table_vlan_${pn}`).append(`<thead class="thead-light"><tr"><th>GW/MASK</th><th>MNG</th><th>HSI</th><th>IPTV</th><th>IMS</th><th>TR069</th><th>NET_ID</th><th>VT_ID</th>`);

            if (cheack_access == 1){
              $(`#data_table_vlan_${pn} .thead-light tr`).append(`<th>Del`);
            }

            $(`#data_table_vlan_${pn}`).append(`<tbody id="data_device_vlan_${pn}">`);
            // console.log(`cheack_access: ${cheack_access}`);
            for (let id_acsw in data[pn]) {
              if (Number(id_acsw)) {
                $(`#data_device_vlan_${pn}`).append(`<tr id="data_tr_vlan_${id_acsw}">`);
                for (let data_vlan in data[pn][id_acsw]) {
                  $(`#data_tr_vlan_${id_acsw}`).append(`<td>${data[pn][id_acsw][data_vlan]}`);
                }
                if (cheack_access == 1){
                  $(`#data_tr_vlan_${id_acsw}`).append(`<td width="2%" ><input id="${id_acsw}" class="btn btn-sm btn-danger delete_pattern" type="button" data-toggle="modal" data-target="#deleteModal" value="-"></input>`);                  
                }
              }
            }
            $(`#pn_${pn}`).append(`<hr class="hr_patterns">`);
          }
        }
        else{
          $('#all_data').empty();
        }
      }
    });
  }
  else{
    $('#all_data').empty();
    $('#DEVICE_ID').val("");
  }
};

$('#clear_all').on('click', function(){
  $('#all_data, #data_networks, #data_vlans').empty();
  $('.form-control').val("");
});

$(document).ready(function() {
  var input = $( '#ip_address' ), timeOut;
  input.on( 'keyup', function () {
    var value = $('#ip_address').val();
    clearTimeout( timeOut ); //если был ввод, перезапускаем наш таймер
    timeOut = setTimeout( function(){
      (value.length >= 4) && get_patterns(); //если таймер отработал, и введено более 8и символов, отправляем запрос
  }, 400 ); // устанавливаем интервал ожидания ввода в миллисекундах
  });
});
$('#ip_address').on('search', function () {
  get_patterns();
});


$('#pattern_add').on('click', function(){
  // console.log('click #pattern_add');
  let device_id = $('#DEVICE_ID').val();
  let network_id = $('#NETWORK_ID').val();
  let vlans_id = $('#VLANS_ID').val();
  if (Number(device_id) && Number(network_id) && Number(vlans_id)) {
    console.log("test" + device_id + " " + network_id + " " + vlans_id);
    $.ajax("add_pattern/", {
      method: "GET",
      data: {device_id: device_id, network_id: network_id, vlans_id: vlans_id},
      cache: false,
      fail: function(){alert("fail");},
      success: function(data){
        console.log(data);
        get_patterns();
      }
    });
  };
});

// $('#data_table_vlan_1').on('click','.delete_pattern', function(){
// $('#data_table_vlan_1 tbody tr td input').click(function(){
$(document).on("click",".delete_pattern", function(){
  let id = $(this).attr("id");
  console.log(`click id ${id}`);
  $('#idPattern').html(id);
  $('.deletePattrnYes').val(id);
});

$(".deletePattrnYes").on("click", function(){
  let id = $(this).attr("value");
  console.log(`yes id ${id}`);
  $.ajax("delete_pattern/", {
    method: "GET",
    data: {id: id},
    cache: false,
    fail: function(){alert("fail");},
    success: function(data){
      if (data != 'Ok'){
        alert(data);
      }
      get_patterns();
    }
  });
});

function show_networks(){
  let netid = $('#NETID').val();
  let mng = $('#MNG').val();
  let vrf = $('#VRF').val();
  let gw_net = $('#GW_NET').val();
  let region = $('#REGION').val();
  if (Number(netid) || Number(mng) || vrf || gw_net || region) {
    $.ajax("get_networks/", {
      method: "GET",
      data: {netid: netid, mng: mng, vrf: vrf, gw_net: gw_net, region: region},
      cache: false,
      fail: function(){alert("fail");},
      success: function(data){
        console.log(data);
        if (Object.keys(data).length != 0){
          $('#data_networks').empty();
          $('#data_networks').append(`<table id="table_networks" class="table table-sm">`);
          for (let id_network in data) {
            $('#NETWORK_ID').val(id_network);
            $('#table_networks').append(`<tbody><tr id="tr_networks_${id_network}">`);
            for (let vlan in data[id_network]) {
              $(`#tr_networks_${id_network}`).append(`<td>${data[id_network][vlan]}`);
            };
          };
        }
        else{
          $('#data_networks').empty();
        }
      }
    });
  }
  else{
    $('#data_networks').empty();
    $('#NETWORK_ID').val("");
  }
};

$(document).ready(function() {
  var input = $( '#networks' ), timeOut;
    input.on( 'keyup', function () {
      clearTimeout( timeOut );
      timeOut = setTimeout( show_networks, 400 );
    });
});

$('#networks').on('search', function () {
  show_networks();
});


function show_vlans(){
  let id_vlan = $('#VLANID').val();
  let hsi_vlan = $('#HSI').val();
  let iptv_vlan = $('#IPTV').val();
  let ims_vlan = $('#IMS').val();
  let tr069_vlan = $('#TR069').val();
  // console.log(hsi_vlan + " " + iptv_vlan + " " + ims_vlan + " " + tr069_vlan);
  if (Number(id_vlan) || Number(hsi_vlan) || Number(iptv_vlan) || Number(ims_vlan) || Number(tr069_vlan)) {
    $.ajax("get_vlans/", {
      method: "GET",
      data: {id: id_vlan, hsi: hsi_vlan, iptv: iptv_vlan, ims: ims_vlan, tr069: tr069_vlan},
      cache: false,
      fail: function(){alert("fail");},
      success: function(data){
        console.log(data);
        if (Object.keys(data).length != 0){
          $('#data_vlans').empty();
          $('#data_vlans').append(`<table id="table_vlans" class="table table-sm">`);
          for (let id_vlan in data) {
            $('#VLANS_ID').val(id_vlan);
            $('#table_vlans').append(`<tbody><tr id="tr_vlans_${id_vlan}">`);
            for (let vlan in data[id_vlan]) {
              $(`#tr_vlans_${id_vlan}`).append(`<td>${data[id_vlan][vlan]}`);
            };
          };
        }
        else{
          $('#data_vlans').empty();
        }
      }
    });
  }
  else{
    $('#data_vlans').empty();
    $('#VLANS_ID').val("");
  }
};

$(document).ready(function() {
  var input = $( '#vlans' ), timeOut;
    input.on( 'keyup', function () {
      clearTimeout( timeOut );
      timeOut = setTimeout( show_vlans, 400 );
    });
});

$('#vlans').on('search', function () {
  show_vlans();
});


$('#vlans_add').on('click', function(){
  // console.log('click #vlans_add');
  let hsi_vlan = $('#HSI').val();
  let iptv_vlan = $('#IPTV').val();
  let ims_vlan = $('#IMS').val();
  let tr069_vlan = $('#TR069').val();
  console.log(hsi_vlan + " " + iptv_vlan + " " + ims_vlan + " " + tr069_vlan);
  if (Number(hsi_vlan) && Number(iptv_vlan) && Number(ims_vlan) && Number(tr069_vlan)) {
    $.ajax("add_patterns_vlans/", {
      method: "GET",
      data: {hsi: hsi_vlan, iptv: iptv_vlan, ims: ims_vlan, tr069: tr069_vlan},
      cache: false,
      fail: function(){alert("fail");},
      success: function(data){
        console.log(data);
        show_vlans();
      }
    });
  };
});


$('#VLANID').mousedown(function(eventObject){
  show_vlans();
});
