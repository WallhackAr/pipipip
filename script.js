// script.js (FINAL)

function generar() {
    // 1. OBTENER VALORES
    const h_e_val = document.getElementById("h_e").value;
    const D_val = document.getElementById("D").value;
    const I_f_val = document.getElementById("I_f").value; 
    const rho_val = document.getElementById("rho").value; 

    const resultadoDiv = document.getElementById("resultado");
    const gif3D = document.getElementById("gif3D");
    const img2D = document.getElementById("img2D"); 

    if (!h_e_val || !D_val || !I_f_val || !rho_val) {
        resultadoDiv.innerHTML = "Error: Por favor, ingrese todos los valores.";
        return;
    }

    resultadoDiv.style.display = "block";
    resultadoDiv.innerHTML = "Generando simulación... Esto puede tomar varios segundos.";
    gif3D.style.display = "none";
    img2D.style.display = "none";

    const r_e_calc = parseFloat(D_val) / 2.0;

    const dataToSend = {
        r_e: r_e_calc,
        h_e: parseFloat(h_e_val),
        I_f: parseFloat(I_f_val),
        rho: parseFloat(rho_val)
    };

    // --- LLAMADA 1: SIMULACIÓN 3D (GIF) ---
    fetch("http://127.0.0.1:5000/simular_3d", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(dataToSend)
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.error); });
        }
        return res.json();
    })
    .then(data => {
        resultadoDiv.innerHTML = "Simulación 3D (GIF) generada. Generando vista 2D...";
        gif3D.src = "http://127.0.0.1:5000/get_gif?name=" + data.filename + "&t=" + new Date().getTime();
        gif3D.style.display = "block";
        
        // --- LLAMADA 2: SIMULACIÓN 2D (PNG) ---
        return fetch("http://127.0.0.1:5000/simular_2d", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(dataToSend)
        });
    })
    .then(res => {
         if (!res.ok) {
            return res.json().then(err => { throw new Error(err.error); });
        }
        return res.json();
    })
    .then(data => {
        resultadoDiv.innerHTML = "Simulación completa. Resultados disponibles.";
        img2D.src = "http://127.0.0.1:5000/get_png?name=" + data.filename + "&t=" + new Date().getTime();
        img2D.style.display = "block";
    })
    .catch(err => {
        resultadoDiv.innerHTML = `Error al generar la simulación. Detalle: ${err.message}`;
        console.error("Error de Fetch:", err);
        gif3D.style.display = "none";
        img2D.style.display = "none";
    });
}