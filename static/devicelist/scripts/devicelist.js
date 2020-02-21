async function get_devicelist() {
  // var result = document.getElementById("model.MES2124_Eltex").innerHTML;
  // console.time('timerName_1');
  // console.time('timerName_2');
  // console.log();
  let ip_address = $('#ip_address').val();
  ip_address = ip_address.replace(/\,/g,'.');
  $('#ip_address').val(ip_address);
  // console.log(`ip_address: ${ip_address}`);
  let hostname = $('#hostname').val();
  let model = $('#model').val();
  let description = $('#description').val();
  let addres = $('#addres').val();
  let office = $('#office').val();
  let status = $('#status').val();
  let uplink = $('#uplink').val();
  let mac = $('#mac').val();
  let limit = $('#limit').val();
  let node = $('#node').val();
  let addres_node = $('#addres_node').val();
  if (status == 'Все'){
    status = ''
  }
  // alert(result);
  // let fias_data = JSON.parse(sessionStorage.getItem('fias_id_key'));
  // console.log(fias_data);
  // console.log(fias_data_get);
  // console.log(fias_data_get['region_fias_id']);
  // console.log(fias_data_get['area_fias_id']);
  // console.log(fias_data_get['city_fias_id']);
  result = ip_address + " " + hostname + " " + model + " " + description + " " + office + " + " + status + " " + uplink + " " + mac + " " + node + " " + addres_node
  // console.log(sessionStorage.getItem('fias_id_key'));
  // console.log(`addres: ${addres}`);
  if (!addres){
    let fias_id = {'region_fias_id' : '',
      'area_fias_id' : '',
      'city_fias_id' : '',
      'settlement_fias_id' : '',
      'street_fias_id' : '',
      'house_fias_id' : '',
    }
    sessionStorage.setItem('fias_id_key', JSON.stringify(fias_id));
  }

  // document.getElementById('result').innerHTML = result;
  // console.timeEnd('timerName_1');
  await $.ajax("get_devicelist/", {
    method: "GET",
    data: {ip_address: ip_address, hostname: hostname, model: model, description: description, office: office, status: status, uplink: uplink, mac: mac, node: node, addres_node: addres_node, limit: limit, addres: sessionStorage.getItem('fias_id_key')},
    // data: {model: model},
    cache: false,
    fail: function(){alert("fail");},
    success: function(data){
      // data = JSON.parse(data);
      // console.log(Date.now());
      // console.timeEnd('timerName_2');
      // console.log(Object.keys(data).length);
      let count = Object.keys(data).length - 1
      $('#data').empty();
      $('#h_ip_address').html(`IP: ${count}`);
      $('#h_ip_address').val(count);
      // document.getElementById('data').innerHTML = ' ';
      for (let ip_address in data) {
        // console.log(ip_address);
        if (ip_address && ip_address != 'access'){
          let class_bg = '';
          if (data[ip_address]['status'] == "Выведен"){
            class_bg = "class=\"table-secondary\"";
          }
          else if (data[ip_address]['status'] == "Монтаж"){
            class_bg = "class=\"table-warning\"";
          }
          else if (data[ip_address]['status'] == "Проект"){
            class_bg = "class=\"table-info\"";
          }
          // if("this_device_id" in sessionStorage){
          //   let deviceid = sessionStorage.getItem('this_device_id');
          //   if(data[ip_address]['id'] == deviceid){
          //     console.log(`data[ip_address]['addres']: ${data[ip_address]['addres']}`);
          //     sessionStorage.setItem('addres_for_modal_window', data[ip_address]['addres']);
          //   }
          // }
          $('#data').append(`<tr ${class_bg} id="${data[ip_address]['id']}">`);
          // console.log(data['uplink']);
          for (let cell in data[ip_address]) {
            if (cell != 'id' && cell != 'latitude' && cell != 'longitude'){

              if (cell == "status" || cell == "date" || cell == "serial" || cell == "ticket"){
                $(`#${data[ip_address]['id']}`).append(`<td class="disable_display">${data[ip_address][cell]}`);                
              }
              else if (cell == "addres" && data[ip_address]['longitude']){
                $(`#${data[ip_address]['id']}`).append(`<td>\
                  <div class="container">\
                    <div class="row">\
                      <div class="device_addres">${data[ip_address][cell]}</div>
                      <div class="col px-2">\
                        <a href="https://yandex.ru/maps/?l=sat%2Cskl&ll=${data[ip_address]['longitude']}%2C${data[ip_address]['latitude']}&mode=whatshere&whatshere%5Bpoint%5D=${data[ip_address]['longitude']}%2C${data[ip_address]['latitude']}&whatshere%5Bzoom%5D=17&z=17" target="YANDEX_MAP">\
                          <img src="/acds/static/geolocation.png" width="22" height="22">\
                        </a>\
                      </div>\
                    </div>\
                  </div>`);
              }
              else{
                $(`#${data[ip_address]['id']}`).append(`<td>${data[ip_address][cell]}`);
              }
            }
          }
          // if (data['access'] == 'yes'){
          $(`#${data[ip_address]['id']}`).append(`<td><a class="edit_device" id="${data[ip_address]['id']}"><img src="/acds/static/gear.png" width="22" height="22"></a>`);
          // }
        }
        
      }
      // if (Object.keys(data).length == 1000){
      //   $('#main_div').append(`<input id="show_more" class="btn btn-dark" type="button" value="show 1000 more">`);
      // }
      // if (Object.keys(data).length < limit){
      //   $('#show_more').remove();
      // }
    }
  });
}

$('#devicelist_submit').on('click', function(){
  get_devicelist();
});

function clear_devicelist() {
  $('#data').empty();
  $('#h_ip_address').html('IP');
  $('#h_ip_address').val('');
}

// после выбора статуса устройства переместить фокус на кнопку FIND
function SetCard(sel) {
  document.getElementById("devicelist_submit").focus();
}

// Открыть окно с данными об устройствк
$(document).on('click', '.edit_device', function(){
  let check = $('#check_argus').html();
  if (check != 'Сравнить с Аргусом'){
    console.log(`check`);
    $('#check_argus').prop("disabled", false);
    $('#check_argus').attr('class','btn btn-primary btn-sm btn-block');
    $('#check_argus').html('Сравнить с Аргусом');
    // $('#check_argus').attr('title', 'Сравнить адрес с данными в Аргусе, в случае если они отличаются от наших, внести изменения.').tooltip('show');
  }
  let deviceid = this.id;
  sessionStorage.setItem('this_device_id', deviceid);

  // test zone  getElementById(deviceid). getElementsByClassName
  // let select = document.getElementById('102379').getElementsByClassName('device_addres').innerHTML;
  // console.log(`select: ${select}`);
  // end test zone
  let uplink = '';
  let port = '';
  let port_uplink = ''

  let ip = $(`#${deviceid} td:eq(0)`).html(),
      hostname = $(`#${deviceid} td:eq(1)`).html(),
      model = $(`#${deviceid} td:eq(2)`).html(),
      description = $(`#${deviceid} td:eq(3) a`).html(),
      addres = $(`#${deviceid} td:eq(4) .device_addres`).html(),
      info = $(`#${deviceid} td:eq(5)`).html(),
      date = $(`#${deviceid} td:eq(6)`).html(),
      status = $(`#${deviceid} td:eq(7)`).html(),
      uplink_and_port = $(`#${deviceid} td:eq(8)`).html(),
      mac = $(`#${deviceid} td:eq(9)`).html(),
      serial = $(`#${deviceid} td:eq(10)`).html();

  if (!description){
    description = $(`#${deviceid} td:eq(3)`).html()
  };
  if (!addres){
    addres = $(`#${deviceid} td:eq(4)`).html()
  };
  if (uplink_and_port != "Null"){
    let res = uplink_and_port.split(" ");
    uplink = res[0];
    port = res[1];
    if (res.length == 4){
      port_uplink = res[3];
    }
  };

  $('#edit_device').modal('show');
  $("#check_argus").show();
  $("#clear_forms").hide();
  $('#device_id').html(`id: ${deviceid}`);
  $('#ip_modal').val(ip);
  $('#model_modal').val(model);
  $('#hostname_modal').val(hostname);
  $('#description_modal').val(description);
  $('#addres_modal').val(addres);
  $('#info_modal').val(info);
  $('#date_modal').val(date);
  $('#status_modal').val(status);
  $('#uplink_modal').val(uplink);
  $('#port_modal').val(port);
  $('#portuplink_modal').val(port_uplink);
  $('#mac_modal').val(mac);
  $('#serial_modal').val(serial);
  if (uplink_and_port == "Null") {
    $("#port_modal").prop("disabled", true);
    $("#portuplink_modal").prop("disabled", true);
  }
});


// Событие на закрытие модального окна
$('#edit_device').on('hidden.bs.modal', function() {
  let check = $('#check_argus').html();
  if (check != 'Сравнить с Аргусом'){
    console.log(`check`);
    $('#check_argus').prop("disabled", false);
    $('#check_argus').attr('class','btn btn-primary btn-sm btn-block');
    $('#check_argus').html('Сравнить с Аргусом');
  }
  let head_modal = $('#device_id').html();
  if (head_modal == 'New device'){
    let all_data = {
        'ip': $('#ip_modal').val(),
        'hostname': $('#hostname_modal').val(),
        'model': $('#model_modal').val(),
        'description': $('#description_modal').val(),
        'addres': $('#addres_modal').val(),
        'info': $('#info_modal').val(),
        'status': $('#status_modal').val(),
        'mac': $('#mac_modal').val(),
        'serial': $('#serial_modal').val()
    };
    sessionStorage.setItem('new_device', JSON.stringify(all_data));
    $('#mac_modal').attr("disabled", false);
  };

  // clear forms
  $('.modal-body .form-control').val('');
  $('#device_id').html('');
});


$('#save_data_device').on('click', function(){
  $('.spinner_load_update').removeClass('d-none');
  let head_modal = $('#device_id').html();
  let url_ajax = 'None'

  let all_data = {
        'ip': $('#ip_modal').val(),
        'hostname': $('#hostname_modal').val(),
        'model': $('#model_modal').val(),
        'description': $('#description_modal').val(),
        'addres': $('#addres_modal').val(),
        'info': $('#info_modal').val(),
        'status': $('#status_modal').val(),
        'uplink': $('#uplink_modal').val(),
        'port': $('#port_modal').val(),
        'port_uplink': $('#portuplink_modal').val(),
        'mac': $('#mac_modal').val(),
        'serial': $('#serial_modal').val()
      };
  console.log(`addres add|edit: ${all_data['uplink']}`);
  if (head_modal == 'New device') {
    url_ajax = 'device_add/';
  }
  else {
    url_ajax = 'device_update/';
    all_data['id'] = sessionStorage.getItem('this_device_id')
  };
  let json_data = JSON.stringify(all_data)

  console.log(`url_ajax: ${url_ajax}`);
  $.ajax({
    url: '/devicelist/' + url_ajax,
    method: "GET",
    data: {all_data: json_data},
    cache: false,
    fail: function(){alert("fail");},
    success: function(data) {
      console.log(`status: ${data['status']}`);
      console.log(`message: ${data['message']}`);
      if (head_modal != 'New device'){
        get_devicelist();
        $('.spinner_load_update').addClass('d-none');
      }
      if (data['status'] == 'ok') {
        get_devicelist();
        $('.spinner_load_update').addClass('d-none');
      }
    }
  });
});


$('#add_new_device').on('click', function(){
  let data_save = JSON.parse(sessionStorage.getItem('new_device'));
  // console.log(`data_save: ${data_save['ip']}`);
  $('#mac_modal').prop("disabled", true);
  if (data_save){
    $('#ip_modal').val(data_save['ip']);
    $('#hostname_modal').val(data_save['hostname']);
    $('#model_modal').val(data_save['model']);
    $('#description_modal').val(data_save['description']);
    $('#addres_modal').val(data_save['addres']);
    $('#info_modal').val(data_save['info']);
    $('#status_modal').val(data_save['status']);
    $('#mac_modal').val(data_save['mac']);
    $('#serial_modal').val(data_save['serial']);
  };
  $('#edit_device').modal('show');
  $("#check_argus").hide();
  $("#clear_forms").show();
  $('#device_id').html('New device');

  let all_data = {
        'ip': $('#ip_modal').val(),
        'hostname': $('#hostname_modal').val(),
        'model': $('#model_modal').val(),
        'description': $('#description_modal').val(),
        'addres': $('#addres_modal').val(),
        'info': $('#info_modal').val(),
        'status': $('#status_modal').val(),
        'mac': $('#mac_modal').val(),
        'serial': $('#serial_modal').val()
      };
  let json_data = JSON.stringify(all_data)

  // $.ajax({
  //   url: "http://10.180.7.34/devicelist/device_add/",
  //   method: "GET",
  //   data: {all_data: json_data},
  //   cache: false,
  //   fail: function(){alert("fail");},
  //   success: function(data){
  //     console.log(`message: ${data['message']}`);
  //     console.log(`error: ${data['error']}`);
  //     get_devicelist();
  //   }
  // });
});

$('#clear_forms').on('click', function(){
  $('.modal-body .form-control').val('');
  return false;
});

$('#check_argus').tooltip();

$('#check_argus').on('click', function(){
  // console.log($('#ip_modal').val());
  let ip = $('#ip_modal').val();
  $('#check_argus').prop("disabled", true);
  $('#check_argus').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Проверка...');
  // $('#check_argus').attr('data-original-title', 'Идёт проверка, ожидайте...').tooltip('show');
  $.ajax({
    url: "/devicelist/fias_data_update/",
    method: "GET",
    data: {ip: ip},
    cache: false,
    fail: function(){alert("fail");},
    error: function (xhr, ajaxOptions, thrownError) {
      alert(`${xhr.status} - ${thrownError}`);
    },
    success: async function(data){
      if (!data['answer']){
        $('#check_argus').attr('class','btn btn-info btn-sm btn-block');
        $('#check_argus').html('Актуально');
        // $('#check_argus').attr('title', 'Изменений не требует').tooltip('show');
      }
      else if (data['answer'] == 'updated'){
        $('#check_argus').attr('class','btn btn-success btn-sm btn-block');
        $('#check_argus').html('Обновлено');
        await get_devicelist();
        let deviceid = sessionStorage.getItem('this_device_id');
        console.log(`deviceid: ${deviceid}`);

        // if("addres_for_modal_window" in sessionStorage){
        //   let addres = sessionStorage.getItem('addres_for_modal_window');
        //   console.log(`addres_for_modal_window: ${addres}`);
        // }
        // else{
        //   let addres = 'Null';
        // }

        // let addres_document = document.getElementById(deviceid).getElementsByClassName('device_addres')[0].innerHTML;
        let addres = $(`#${deviceid} td:eq(4) .device_addres`).html();
        // console.log(`addres_document: ${addres_document}`);
        console.log(`addres_jqure: ${addres}`);

        // console.log(`addres: ${addres}`);
        $('#addres_modal').val(addres);
      }
      else{
        $('#check_argus').attr('class','btn btn-danger btn-sm btn-block');
        $('#check_argus').html('Ошибка');
        console.log(data['answer']);
      }
    }
  });
  return false;
});


$(".address_dadata").suggestions({
  token: "4050395393551c7931ceabf9015365c473c8879b",
  type: "ADDRESS",
  deferRequestBy: 300,
  minChars: 4,
  constraints: {
    label: "Урал",
    // ограничиваем поиск по коду ФИАС
    locations: [
      {"region_fias_id": "54049357-326d-4b8f-b224-3c6dc25d6dd3"},
      {"region_fias_id": "4a3d970f-520e-46b9-b16c-50d4ca7535a8"},
      {"region_fias_id": "826fa834-3ee8-404f-bdbc-13a5221cfb6e"},
      {"region_fias_id": "4f8b1a21-e4bb-422f-9087-d3cbf4bebc14"},
      {"region_fias_id": "27eb7c10-a234-44da-a59c-8b1f864966de"},
      {"region_fias_id": "92b30014-4d52-4e2e-892d-928142b924bf"},
      {"region_fias_id": "d66e5325-3a25-4d29-ba86-4ca351d9704b"},
      // {"region_fias_id": "волгоградская"},
      // {"region_fias_id": "калмыкия"},
      // {"region_fias_id": "краснодарский"},
      // {"region_fias_id": "ростовская"}
    ],
    deletable: true
  },
  // locations: [{"region_fias_id": "54049357-326d-4b8f-b224-3c6dc25d6dd3"}]
  /* Вызывается, когда пользователь выбирает одну из подсказок */
  onSelect: function(suggestion) {
    // region_fias_id = suggestion['data']['region_fias_id']
    // area_fias_id = suggestion['data']['area_fias_id']
    // city_fias_id = suggestion['data']['city_fias_id']
    // settlement_fias_id = suggestion['data']['settlement_fias_id']
    // street_fias_id = suggestion['data']['street_fias_id']
    // house_fias_id = suggestion['data']['house_fias_id']
    // fias_id = suggestion['data']['fias_id']

    let fias_id = {'region_fias_id' : suggestion['data']['region_fias_id'],
        'area_fias_id' : suggestion['data']['area_fias_id'],
        'city_fias_id' : suggestion['data']['city_fias_id'],
        'settlement_fias_id' : suggestion['data']['settlement_fias_id'],
        'street_fias_id' : suggestion['data']['street_fias_id'],
        'house_fias_id' : suggestion['data']['house_fias_id'],
      }

    sessionStorage.setItem('fias_id_key', JSON.stringify(fias_id));

    // console.log(fias_id);
    // let fias_data = JSON.parse(sessionStorage.getItem('fias_id_key'));
    // console.log(fias_data);

    $("#alert_address").addClass('show');
    $("#submit").prop("disabled", true);
    $("span.bdg_address").remove();
    $("div.block_address").append("<span class='badge badge-danger bdg_address'>error</span>");


  }
});

$(".scrolltop").click(function() {
  $("html, body").animate({ scrollTop: 0 }, "slow");
  return false;
});


$("#model_modal").autocomplete({
  delay:300,
  minLength:3,
  source: function( request, response ) {
    $.ajax({
      url: "/activator/get_model/",
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
    $("#alert_model").removeClass('show');
    $("#submit").prop("disabled", false);
    $("span.bdg_model").remove();
    $("div.block_model").append("<span class='badge badge-success bdg_model'>ok</span>");
  }
});

$( "#model_modal" ).autocomplete( "option", "appendTo", ".model_autocomplete" );
$('.spinner_load_update').modal('hide');


$('#uplink_modal').keyup(function () {
  modal_uplink = $('#uplink_modal').val();
  console.log(modal_uplink);
  if (!modal_uplink) {
    $("#port_modal").prop("disabled", true);
    $("#portuplink_modal").prop("disabled", true);
  }
  else {
    $("#port_modal").prop("disabled", false);
    $("#portuplink_modal").prop("disabled", false);    
  }

})