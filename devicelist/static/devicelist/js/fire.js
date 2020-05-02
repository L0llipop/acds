$(document).on('click','.edit_fire', function () {//показывает модальное окно с заполнеными данными
  event.preventDefault();
  let deviceid = this.id;
  let all_data = JSON.parse(document.getElementById("fireid"+deviceid).value);
  //let firetypeedit = document.forms["editfireform"].elements["firetype_modal"];
  
  if (all_data['type']=='ОУ'){document.forms["editfireform"].getElementsByTagName('option')[0].selected = 'selected';}
  if (all_data['type']=='ОП'){document.forms["editfireform"].getElementsByTagName('option')[1].selected = 'selected';}
  if (all_data['type']=='ОВМ'){document.forms["editfireform"].getElementsByTagName('option')[2].selected = 'selected';}
  
  if (all_data['status']=='Готов'){document.forms["editfireform"].getElementsByTagName('option')[3].selected = 'selected';}
  if (all_data['status']=='на складе'){document.forms["editfireform"].getElementsByTagName('option')[4].selected = 'selected';}
  if (all_data['status']=='потерян'){document.forms["editfireform"].getElementsByTagName('option')[5].selected = 'selected';}
  if (all_data['status']=='разряжен'){document.forms["editfireform"].getElementsByTagName('option')[6].selected = 'selected';}
  if (all_data['status']=='сломан'){document.forms["editfireform"].getElementsByTagName('option')[7].selected = 'selected';}
  
  if (all_data['fireclass'].indexOf('А') !=  -1 ){document.forms["editfireform"].getElementsByTagName('option')[8].selected = 'selected';}
    else {document.forms["editfireform"].getElementsByTagName('option')[8].selected = '';}
  if (all_data['fireclass'].indexOf('В') !=  -1 ){document.forms["editfireform"].getElementsByTagName('option')[9].selected = 'selected';}
    else{document.forms["editfireform"].getElementsByTagName('option')[9].selected = '';}
  if (all_data['fireclass'].indexOf('Д') !=  -1 ){document.forms["editfireform"].getElementsByTagName('option')[10].selected = 'selected';}
    else{document.forms["editfireform"].getElementsByTagName('option')[10].selected = '';}
  if (all_data['fireclass'].indexOf('С') !=  -1 ){document.forms["editfireform"].getElementsByTagName('option')[11].selected = 'selected';}
    else {document.forms["editfireform"].getElementsByTagName('option')[11].selected = '';}
  if (all_data['fireclass'].indexOf('Е') !=  -1 ){document.forms["editfireform"].getElementsByTagName('option')[12].selected = 'selected';}
    else{document.forms["editfireform"].getElementsByTagName('option')[12].selected = '';}
  
  
  document.forms["editfireform"].elements["fireid"].value = deviceid;
  document.forms["editfireform"].elements["addres_modal"].value = all_data['address'];
  document.forms["editfireform"].elements["room_modal"].value = all_data['room'];
  document.forms["editfireform"].elements["comandor_modal"].value = all_data['comandor'];
  document.forms["editfireform"].elements["serial_modal"].value = all_data['serial'];
  document.forms["editfireform"].elements["inventory_modal"].value = all_data['inventory'];
  document.forms["editfireform"].elements["weight_modal"].value = all_data['fullweight'];
  //document.forms["editfireform"].getElementsByTagName('option')[1].selected = 'selected';
  //document.forms["editfireform"].elements["firetype_modal"].option('powdery').selected = true;
  modal_edit.style.display = "block";
});

function editfire(){ // нужно дописать
  event.preventDefault();
  var fireclasslist = $('#fireclass_modal option:selected').toArray().map(item => item.value).join();
 all_data = {
   'action': "editfire",
   'fireid': document.forms["editfireform"].elements["fireid"].value,
   'address': document.forms["editfireform"].elements["addres_modal"].value,
   'room': document.forms["editfireform"].elements["room_modal"].value,
   'comandor': document.forms["editfireform"].elements["comandor_modal"].value,
   'serial': document.forms["editfireform"].elements["serial_modal"].value,
   'inventory': document.forms["editfireform"].elements["inventory_modal"].value,
   'weight': document.forms["editfireform"].elements["weight_modal"].value,
   'firetype': document.forms["editfireform"].elements["firetype_modal"].value,
   'firestatus': document.forms["editfireform"].elements["firestatus_modal"].value,
   'fireclass':fireclasslist
 }

 let json_data = JSON.stringify(all_data);

  

 $.ajax('set_fire_data/',{
   method: "GET",
   data: {all_data: json_data},
   cache: false,
   fail: function(){alert('что-то подгорело');},
   success: function(data) {
     console.log(data['result']);
     if (data['edit'] == 'ok'){
       document.getElementById("editfire_modal").setAttribute('style', 'color: green');
       function nothing(){
         document.getElementById("editfire_modal").setAttribute('style', 'color: wight');
         //document.forms.addfire_modal.reset();
         document.forms.namedItem("editfireform").reset();
         modal_edit.style.display = "none";
         }
       setTimeout(nothing,1000);
      
       }
     if (data['error'] !== undefined) {
       document.getElementById("editfire_modal").setAttribute('style', 'color: red');
       function nothing(){
         document.getElementById("editfire_modal").setAttribute('style', 'color: wight');
         }
       setTimeout(nothing,2000);
       console.log(data['error']);
       }
   }
 });

}



$(document).on('click','.add_check', function () {
  event.preventDefault();
  let deviceid = this.id;
  document.forms["addfirecheck"].elements["fireid"].value = deviceid;
  document.forms["addfirecheck"].elements["firedata_check"].value = new Date().toLocaleDateString('en-CA');
  //document.forms["addfirecheck"].elements["comandor_check"].value = new Date().toLocaleDateString('en-CA');
  modal_check.style.display = "block";

});

function addfirecheck(){
  event.preventDefault();
  let all_data = {
        'action': "insertcheck",
        'fireid': document.forms["addfirecheck"].elements["fireid"].value,
        'data': document.forms["addfirecheck"].elements["firedata_check"].value,
        'comandor': document.forms["addfirecheck"].elements["comandor_check"].value,
        'weight': document.forms["addfirecheck"].elements["firechecked_weght"].value,
        'firecheck_type': document.forms["addfirecheck"].elements["firecheck_type"].value
      };
  let json_data = JSON.stringify(all_data);

	$.ajax("set_fire_data/", {
		method: "GET",
		data: {all_data: json_data}, 
		cache: false,
		fail: function(){alert('проверка не прошла');},
		success: function(data) {
      if (data['insert'] == 'ok'){
        //console.log(data['class'] );
        document.getElementById("addfire_check").setAttribute('style', 'color: green');
        function nothing(){
          document.getElementById("addfire_check").setAttribute('style', 'color: wight');
          document.forms.namedItem("addfirecheck").reset();
          //document.getElementById("firecheckid"+all_data['fireid']).textContent =  document.getElementById("firecheckid"+all_data['fireid']).textContent + all_data['firecheck_type'] + " " + all_data['data'] + all_data['weight']  + " "+all_data['comandor'] + "<br>"
          modal_check.style.display = "none";
          }
        setTimeout(nothing,1000);
       
        }
      if (data['error'] !== undefined) {
        document.getElementById("addfire_check").setAttribute('style', 'color: red');
        function nothing(){
          document.getElementById("addfire_check").setAttribute('style', 'color: wight');
          }
        setTimeout(nothing,2000);
        console.log(data['error']);
        }
		}
	})
	
	
}






// Get the modal
var modal = document.getElementById("myModal");
var modal_check = document.getElementById("modaladdcheck");
var modal_edit = document.getElementById("modaleditfire");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];
var span_check = document.getElementsByClassName("close_check")[0];
var span_edit = document.getElementsByClassName("close_edit")[0];

// When the user clicks on the button, open the modal
btn.onclick = function() {
  modal.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}
span_check.onclick = function() {
  modal_check.style.display = "none";
}
span_edit.onclick = function() {
  modal_edit.style.display = "none";
}


// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if ((event.target == modal) || (event.target == modal_check) || (event.target == modal_edit)) {
    modal.style.display = "none";
    modal_check.style.display = "none";
    modal_edit.style.display = "none";
  }
}



function addfire(){
//  document.forms["addfireform"].elements["addres_modal"].value
  event.preventDefault();
  var fireclasslist = $('#fireclass_modal option:selected').toArray().map(item => item.value).join();
  let all_data = {
        'action': "insertnew",
        'address': document.forms["addfireform"].elements["addres_modal"].value,
        'room': document.forms["addfireform"].elements["room_modal"].value,
        'comandor': document.forms["addfireform"].elements["comandor_modal"].value,
        'serial': document.forms["addfireform"].elements["serial_modal"].value,
        'inventory': document.forms["addfireform"].elements["inventory_modal"].value,
        'weight': document.forms["addfireform"].elements["weight_modal"].value,
        'firetype': document.forms["addfireform"].elements["firetype_modal"].value,
        'firestatus': document.forms["addfireform"].elements["firestatus_modal"].value,
        'fireclass':fireclasslist
      };


  let json_data = JSON.stringify(all_data);

  

  $.ajax('set_fire_data/',{
    method: "GET",
    data: {all_data: json_data},
    cache: false,
    fail: function(){alert('что-то подгорело');},
    success: function(data) {
      console.log(data['result']);
      if (data['insert'] == 'ok'){
        document.getElementById("addfire_modal").setAttribute('style', 'color: green');
        function nothing(){
          document.getElementById("addfire_modal").setAttribute('style', 'color: wight');
          //document.forms.addfire_modal.reset();
          document.forms.namedItem("addfireform").reset();
          modal.style.display = "none";
          }
        setTimeout(nothing,1000);
       
        }
      if (data['error'] !== undefined) {
        document.getElementById("addfire_modal").setAttribute('style', 'color: red');
        function nothing(){
          document.getElementById("addfire_modal").setAttribute('style', 'color: wight');
          }
        setTimeout(nothing,2000);
        console.log(data['error']);
        }
    }
  });
};

var btnexcel = document.getElementById("Btnfirejornal");

btnexcel.onclick = function() {
  var link = document.createElement("a");
  link.download = "firejornal.xlsx";
  link.href = "http://10.180.7.34/devicelist/fire/firejornal/?firelist="+fireidlist;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  delete link;
}


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
    ],
    deletable: true
  },
  // locations: [{"region_fias_id": "54049357-326d-4b8f-b224-3c6dc25d6dd3"}]
  /* Вызывается, когда пользователь выбирает одну из подсказок */
  onSelect: function(suggestion) {


    let fias_id = {'region_fias_id' : suggestion['data']['region_fias_id'],
        'area_fias_id' : suggestion['data']['area_fias_id'],
        'city_fias_id' : suggestion['data']['city_fias_id'],
        'settlement_fias_id' : suggestion['data']['settlement_fias_id'],
        'street_fias_id' : suggestion['data']['street_fias_id'],
        'house_fias_id' : suggestion['data']['house_fias_id'],
      }

    sessionStorage.setItem('fias_id_key', JSON.stringify(fias_id));



  }
});

$(".fire_dadata").suggestions({
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
    ],
    deletable: true
  },
  // locations: [{"region_fias_id": "54049357-326d-4b8f-b224-3c6dc25d6dd3"}]
  /* Вызывается, когда пользователь выбирает одну из подсказок */
  onSelect: function(suggestion) {


    let fias_id = {'region_fias_id' : suggestion['data']['region_fias_id'],
        'area_fias_id' : suggestion['data']['area_fias_id'],
        'city_fias_id' : suggestion['data']['city_fias_id'],
        'settlement_fias_id' : suggestion['data']['settlement_fias_id'],
        'street_fias_id' : suggestion['data']['street_fias_id'],
        'house_fias_id' : suggestion['data']['house_fias_id'],
      }
    document.getElementById('fire_fias').value = JSON.stringify(fias_id);
    //sessionStorage.setItem('fias_id_key', JSON.stringify(fias_id));



  }
});