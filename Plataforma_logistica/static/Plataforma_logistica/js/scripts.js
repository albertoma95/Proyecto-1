// static/Plataforma_logistica/js/scripts.js

document.addEventListener("DOMContentLoaded", function () {
    // Manejar el botón de generar pedidos
    document.getElementById("btn-generar-pedidos").addEventListener("click", function (event) {
        event.preventDefault(); // Evitar que el formulario recargue la página

        fetch("/Plataforma_logistica/generar_pedidos/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}), // Enviar datos si es necesario
        })
            .then((response) => response.json())
            .then((data) => {
                alert(data.message); // Mostrar mensaje de éxito
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("Algo salió mal.");
            });
    });

    // Manejar el botón de calcular rutas
    document.getElementById("btn-calcular-rutas").addEventListener("click", function (event) {
        event.preventDefault();

        fetch("/Plataforma_logistica/calcular_rutas/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.mapa_html) {
                    document.getElementById("mapa").innerHTML = data.mapa_html; // Actualizar el mapa
                } else if (data.error) {
                    alert(data.error);
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("Algo salió mal.");
            });
    });

    // Función para obtener el CSRF token de las cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
