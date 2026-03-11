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

})

}
