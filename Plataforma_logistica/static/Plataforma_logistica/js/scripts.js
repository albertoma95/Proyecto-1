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

        // Capturar valores de los campos
        const velocidad = document.getElementById("input-velocidad").value;
        const capacidad = document.getElementById("input-capacidad").value;
        const costeKm = document.getElementById("input-coste-km").value;

        // Validación adicional
        if (!velocidad || velocidad <= 0) {
            alert("La velocidad debe ser mayor que 0.");
            return;
        }

        if (!capacidad || capacidad <= 0) {
            alert("La capacidad debe ser mayor que 0.");
            return;
        }

        if (!costeKm || costeKm <= 0) {
            alert("El coste por kilómetro debe ser mayor que 0.");
            return;
        }

        fetch("/Plataforma_logistica/calcular_rutas/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                velocidad: velocidad,
                capacidad: capacidad,
                coste_km: costeKm,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.mapa_html) {
                    document.getElementById("mapa").innerHTML = data.mapa_html;

                    const trucksInfo = data.trucks_info;
                    const trucksPerPage = 6;
                    let currentPage = 1;

                    function renderTrucks(page) {
                        const trucksContainer = document.getElementById("trucks-container");
                        trucksContainer.innerHTML = ''; // Limpiar el contenido actual

                        const start = (page - 1) * trucksPerPage;
                        const end = start + trucksPerPage;
                        const trucksToShow = trucksInfo.slice(start, end);

                        trucksToShow.forEach((truck) => {
                            // Crear la tarjeta para cada camión
                            let truckHtml = `
                                <div class="col-md-4 mb-4">
                                    <div class="card">
                                        <div class="card-body">
                                            <h5 class="card-title">Camión ${truck.truck_number}</h5>
                                            <p><strong>Día de inicio de reparto:</strong> ${truck.start_date}</p>
                                            <p><strong>Días totales de la ruta:</strong> ${truck.total_days}</p>
                                            
                                            <!-- Botón para ver más detalles -->
                                            <button class="btn btn-primary btn-sm view-truck-info" type="button" data-truck-id="${truck.truck_number}">
                                                Más información
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            `;
                            trucksContainer.innerHTML += truckHtml;
                        });

                        // Actualizar la paginación
                        updatePagination(page);
                    }

                    function updatePagination(page) {
                        const pagination = document.getElementById("pagination");
                        pagination.innerHTML = ''; // Limpiar los botones de paginación actuales

                        const totalPages = Math.ceil(trucksInfo.length / trucksPerPage);

                        // Botones de paginación
                        for (let i = 1; i <= totalPages; i++) {
                            const pageItem = document.createElement("li");
                            pageItem.classList.add("page-item");
                            if (i === page) {
                                pageItem.classList.add("active");
                            }
                            pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
                            pageItem.addEventListener("click", () => renderTrucks(i));
                            pagination.appendChild(pageItem);
                        }
                    }

                    const modal = new bootstrap.Modal(document.getElementById('truckModal'));

                    document.body.addEventListener("click", (event) => {
                        if (event.target.classList.contains("view-truck-info")) {
                            const truckId = event.target.getAttribute("data-truck-id");
                            const truck = trucksInfo.find(t => t.truck_number == truckId);
                            
                            if (truck) {
                                // Crear contenido dinámico para el modal
                                let modalContent = `
                                    <h5>Camión ${truck.truck_number}</h5>
                                    <p><strong>Día de inicio de reparto:</strong> ${truck.start_date}</p>
                                    <p><strong>Días totales de la ruta:</strong> ${truck.total_days}</p>
                                    <h6>Órdenes:</h6>
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
                                `;

                                // Insertar contenido en el modal
                                document.getElementById("truckModalBody").innerHTML = modalContent;

                                // Mostrar el modal
                                modal.show();
                            }
                        }
                    });

                    // Cerrar el modal manualmente si es necesario
                    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
                        button.addEventListener("click", () => {
                            modal.hide();
                        });
                    });

                    renderTrucks(currentPage);
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
