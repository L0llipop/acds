
$(document).ready(function(){
  $.ajax("http://10.180.7.34/devicelist/maps/get_data", {
   method: "GET",
   data: {},
   cache: false,
   fail: function(){},
   success: function(data){
    DG.then(function() {
        // загрузка кода модуля
        return DG.plugin('https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js');
    }).then(function() {
      map = DG.map('map', {center: [57.151184, 65.547212], zoom: 16, geoclicker:true});
      var markers = DG.markerClusterGroup();  
      $.each(data, function(key, value) { 
        ip = value['ip'];
        model = value['model'];
        var marker = DG.marker([value['lat'], value['lon']], { title : model });
        marker.bindPopup(ip);
        markers.addLayer(marker);
        map.addLayer(markers);
      });
    });
   }
	});
});

document.getElementById("showServices").onclick = function(){
  $.ajax("http://10.180.7.34/devicelist/maps/get_service_data", {
   method: "GET",
   data: {},
   cache: false,
   fail: function(){},
   success: function(data){
	DG.then(function() {
		var  markers = DG.featureGroup();
		$.each(data, function(key, value) {
			if (value['cap'] !==  null) {
				var percentInet = Number(((value['inet']/value['cap']) * 100).toFixed(1))
				var percentTV = Number(((value['iptv']/value['cap']) * 100 ).toFixed(1))
				var percentIMS = Number(((value['ims']/value['cap'] ) * 100).toFixed(1))
				services = "<nobr>"+"Int-"+value['inet'] + " TV-"+value['iptv'] + " IMS-"+ value['ims']+" Vol-"+ value['cap'] +"</nobr><br><nobr>  Процент "+ percentInet.toString() + "% "+ percentTV.toString()+ "% " + percentIMS.toString()+"%</nobr>";
			}
			else {
				services = "<nobr>"+"Int-"+value['inet'] + " TV-"+value['iptv'] + " IMS-"+ value['ims']+"</nobr><br>"+"Ёмкость не известна";
			}
			//-----------------------
			DG.popup({closeButton:false, className:'popservice'})
				.setLatLng([value['lat'], value['lon']])
				.setContent(services)
				.addTo(markers);
			map.addLayer(markers);});
       //----------------------------
       // var marker = DG.marker([value['lat'], value['lon']], { title : services });
       // marker.bindPopup(services);
        // markers.addLayer(marker);
        //map.addLayer(markers); });
      // getBounds();  получить текущие координаты

      });
    }
   });
}