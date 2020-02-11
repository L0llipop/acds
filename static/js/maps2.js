
$(document).ready(function(){
  event.preventDefault();
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
      map = DG.map('map', {
        center: [57.151184, 65.547212],
        zoom: 16
      });
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