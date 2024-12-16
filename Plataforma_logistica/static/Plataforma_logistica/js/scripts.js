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
                    document.getElementById("mapa").innerHTML = data.mapa_html;

                    const trucksInfo = data.trucks_info;
                    const trucksContainer = document.getElementById("trucks_info");
                    trucksContainer.innerHTML = ''; 

                    trucksInfo.forEach(truck => {
                        // Crear un HTML para cada camión
                        let truckHtml = `
                            <div class="card truck-card">
                                <div class="card-body">
                                    <h5 class="card-title">Camión ${truck.truck_number}</h5>
                                    <p><strong>Día de inicio de reparto:</strong> ${truck.start_date}</p>
                                    <p><strong>Días totales de la ruta:</strong> ${truck.total_days}</p>
                                    
                                    <!-- Botón para togglear la información detallada -->
                                    <button class="btn btn-primary btn-sm" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTruck_${truck.truck_number}" aria-expanded="false" aria-controls="collapseTruck_${truck.truck_number}">
                                        Más información
                                    </button>
                                    
                                    <!-- Sección colapsable con la información de los días y pedidos -->
                                    <div class="collapse mt-3" id="collapseTruck_${truck.truck_number}">
                                        ${truck.daily_orders.map(dayData => `
                                            <h6>Día ${dayData.day_num}:</h6>
                                            ${dayData.orders.length > 0 ? `
                                                <ul class="list-group list-group-flush mb-3">
                                                    ${dayData.orders.map(order => `
                                                        <li class="list-group-item">
                                                            Pedido ${order.id} - Caduca: ${order.expiration_date}
                                                        </li>
                                                    `).join('')}
                                                </ul>
                                            ` : `<p>Sin entregas este día.</p>`}
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                        `;

                        // Agregar el HTML del camión al contenedor
                        trucksContainer.innerHTML += truckHtml;
                    });

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
