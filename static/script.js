document.getElementById("form").addEventListener("submit",function(e){

e.preventDefault()

let distancia = document.getElementById("distancia").value
let veiculo = document.getElementById("veiculo").value

let formData = new FormData()
formData.append("distancia",distancia)
formData.append("veiculo",veiculo)

fetch("/calcular",{

method:"POST",
body:formData

})
.then(res=>res.json())
.then(data=>{

document.getElementById("valor").innerText =
"Valor estimado: R$ "+data.valor

})

})
