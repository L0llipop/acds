function get_massconfig() {
  let net_login = $('#login').val();
  let net_password = $('#password').val();
  let ip_list = $('#iplist').val();
  let findtext = $('#findtext').val();
  let command_list = $('#command_list').val();

  result = net_login + " " + ip_list + " " + command_list
  //console.log(result);

  event.preventDefault();
  //$.ajax("mass_config_send/", {method: "GET", data: {net_login: net_login, net_password: net_password, ip_list: ip_list, command_list: command_list}, 
  //cache: false, 
  //fail: function(){alert("fail");} });
  
  $.ajax("mass_config_send/", {
   method: "GET",
   data: {net_login: net_login, net_password: net_password, ip_list: ip_list, findtext:findtext, command_list: command_list},
   cache: false,
   fail: function(){document.getElementById("command_output").value = "что-то пошло не так";},
   success: function(data1){
        console.log(data1);
				document.getElementById("command_output").value = data1['result']+ "\nСтрока не найдена\n" + data1['strfinded'] + "\n \nСтрока найдена\n"+data1['strnotfind'] + "\n \n Login fail: " +data1['fail'] ;
		}
	});
  
  ;
}
