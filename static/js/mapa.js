let mapa

function initMap(){

mapa = new google.maps.Map(document.getElementById("mapa"),{

center:{lat:-23.5505,lng:-46.6333},
zoom:12

})

}

window.onload = initMap
