function calcular(){

let coleta=document.getElementById("coleta").value
let entrega=document.getElementById("entrega").value

let form=new FormData()

form.append("coleta",coleta)
form.append("entrega",entrega)

fetch("/calcular_distancia",{
method:"POST",
body:form
})

.then(r=>r.json())
.then(d=>{

document.getElementById("distancia").value=d.km

var map=L.map('map').setView([d.lat1,d.lon1],11)

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

var poly=L.polyline([
[d.lat1,d.lon1],
[d.lat2,d.lon2]
]).addTo(map)

map.fitBounds(poly.getBounds())

})

}
