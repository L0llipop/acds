let userName = $('#username').val();
console.log(`username: ${userName}`);

let chatSocket = new WebSocket(
    'ws://' + window.location.host +
    '/ws/topology/' + userName + '/');
console.log(chatSocket)

chatSocket.onmessage = function(e) {
    let data = JSON.parse(e.data);
    // let data = e;
    data = JSON.parse(data['message']);
    console.log(data);
    let count = data['count'];
    let previous_port = count - 1;
    let next_port = count + 1;
    console.log('===============', data['time'], '===============');
    if (data['status'] == 'error') {
        $('#spinner').remove();
        $(`#topology_submit`).prop('disabled', false);
        $(`#topology_submit`).val('FIND');
        $(`#error`).html(data['message_error']);
        if (count in data && 'desc' in data[count]) {  //если ошибка, то покажет последний хост
            $("#result").append(`<div class="col-12 justify-content-center align-items-center text-center result_topology" id="count_${count}">`);
            $(`#count_${count}`).append(`<div class="col-auto">\u2B06`);
            $(`#count_${count}`).append(`<div class="col-12">${data[count]['desc']}&emsp;${data[count]['ip']}&emsp;${data[count]['model']}`);
        }
        return;
    }
    if (data['status'] == 'ok') {
        console.log('End');
    }

    let ip = $('#ipaddress').html(),
        hostname = $('#hostname').html(),
        model = $('#model').html(),
        vrf = $('#vrf').html(),
        mac = $('#mac').html(),
        vlan = $('#vlan').html(),
        tunnel_vlan = $('#tunnel_vlan').html();

    // if (!ip) {
    $('#ipaddress').html(data['ip'])
    // };
    if (!hostname && data['hostname']) {
        $('#hostname').html(data['hostname'])
    };
    if (!model && data['model']) {
        $('#model').html(data['model'])
    };
    if (!vrf && data['vrf']) {
        $('#vrf').html(data['vrf'])
    };
    if (!mac && data['mac']) {
        $('#mac').html(data['mac'])
    };
    if (!vlan && data['vlan']) {
        $('#vlan').html(data['vlan'])
    };
    if (!tunnel_vlan && data['tunnel_vlan']) {
        $('#tunnel_vlan').html(data['tunnel_vlan'])
    };


    if (count >= 1 && data['status'] != 'ok'){
        // console.log("---1---")
        $("#result").append(`<div class="col-12 justify-content-center align-items-center text-center result_topology" id="count_${count}">`);

        // if (count == 1 && data['status'] == 'error') {
        //     // console.log("---1-4---")
        //     $('#spinner').remove();
        //     $(`#topology_submit`).prop('disabled', false);
        //     $(`#topology_submit`).val('FIND');
        //     $(`#error`).html(data['message_error']);
        // }
        if (data[count]['port_uplink']) {
            // console.log("---1-2---")
            $(`#count_${count}`).append(`<div class="col-auto">\u2B06`);
            $(`#count_${count}`).append(`<div class="col-auto">${data[count]['port_uplink']}`);
        }
        if (count in data && 'desc' in data[count]) {
            // console.log("---1-3---")
            $(`#count_${count}`).append(`<div class="col-12">${data[count]['desc']}&emsp;${data[count]['ip']}&emsp;${data[count]['model']}`);
        }
        if (previous_port in data && 'port' in data[previous_port] && count == 1) {
            // console.log("---1-1---")
            $(`#count_${count}`).append(`<div class="col-auto">${data[previous_port]['port']}`);
            // $(`#count_${count}`).append(`<div class="col-auto">\u2B06`);
        }

        if (count in data && 'port' in data[count]) {
            // console.log("---1-1---")
            $(`#count_${count}`).append(`<div class="col-auto">${data[count]['port']}`);
            // $(`#count_${count}`).append(`<div class="col-auto">\u2B06`);
        }
        // if (next_port in data && 'desc' in data[next_port]) {
        //     $(`#count_${count}`).append(`<div class="col-12">${data[next_port]['desc']}&emsp;${data[next_port]['ip']}&emsp;${data[next_port]['model']}`);
        // }

    }

    if ((count in data && 'ip' in data[count] && data[count]['ip'] == $('#ip_address').val()) || (data['status'] == 'error' || data['status'] == 'ok')) {
        // console.log("---2---")
        $('#spinner').remove();
        $(`#topology_submit`).prop('disabled', false);
        $(`#topology_submit`).val('FIND');
        $(`#error`).html(data['message_error']);
    }

    console.log(`count: ${count}| previous_port: ${previous_port}| next_port: ${next_port}`);
    // $(`#error`).html(data['message_error']);

};

chatSocket.onopen = function(e) {
    console.log('Open websocket');
    $(`#topology_submit`).prop('disabled', false);
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
    $(`#topology_submit`).prop('disabled', true);
    $('#spinner').remove();
    alert("Необходимо обновить страницу");
};



document.querySelector('#ip_address').focus();
document.querySelector('#ip_address').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#topology_submit').click();
    }
};
document.querySelector('#topology_submit').onclick = function(e) {
    let messageInputDom = document.querySelector('#ip_address');
    console.log(`messageInputDom: ${messageInputDom}`);
    let message = messageInputDom.value;
    let checked = $('#online').prop('checked');
    chatSocket.send(JSON.stringify({
        'message': message,
        'online': checked,
        'username': userName,
    }));

    $(`#error`).html('wait');
    $('#hostname').html('');
    $('#model').html('');
    $('#vrf').html('');
    $('#mac').html('');
    $('#vlan').html('');
    $('#tunnel_vlan').html('');
    $('.result_topology').remove();


    $(`#topology_submit`).prop('disabled', true);
    $(`#topology_submit`).val('Wait');
    $(`#forma`).append(`<div id="spinner" class="spinner-border text-primary" role="status"><span class="sr-only"></span></div>`);
};


$('#online').on('click', function(){
    let checked = $('#online').prop('checked');
    console.log(`checked: ${checked}`);
});
