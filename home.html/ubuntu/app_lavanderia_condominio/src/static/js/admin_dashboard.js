// /home/ubuntu/app_lavanderia_condominio/src/static/js/admin_dashboard.js
document.addEventListener("DOMContentLoaded", () => {
    const bookingsTableBody = document.getElementById("bookings-table-body");
    const laundriesTableBody = document.getElementById("laundries-table-body");
    const filterDateStart = document.getElementById("filter-date-start");
    const filterDateEnd = document.getElementById("filter-date-end");
    const filterFloorSelect = document.getElementById("filter-floor");
    const applyFiltersBtn = document.getElementById("apply-filters-btn");

    // Checar se o usuário é admin e tem acesso (o backend já faz isso, mas pode ser um check extra)
    // Para simplificar, vamos assumir que se a página carregou, o backend permitiu.

    async function fetchWithAuth(url, options = {}) {
        // Idealmente, o frontend saberia se está autenticado e enviaria cookies automaticamente.
        // Se precisar de token JWT, adicionaria ao header Authorization aqui.
        const response = await fetch(url, options);
        if (response.status === 401 || response.status === 403) {
            alert("Acesso não autorizado ou sessão expirada. Faça login como administrador.");
            window.location.href = "/"; // Redireciona para a página principal/login
            return null;
        }
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            console.error("Erro na API:", response.status, errorData);
            alert(`Erro ao buscar dados: ${errorData?.error || response.statusText}`);
            return null;
        }
        return response.json();
    }

    async function loadFloors() {
        const floors = await fetchWithAuth("/api/admin/floors");
        if (floors) {
            filterFloorSelect.innerHTML = 
                floors.map(floor => `<option value="${floor.numero_andar}">${floor.numero_andar}</option>`).join("");
            filterFloorSelect.insertAdjacentHTML("afterbegin", 
                `<option value="">Todos os Andares</option>`
            );
        }
    }

    async function loadBookings() {
        bookingsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Carregando agendamentos...</td></tr>`;
        let url = "/api/admin/all_bookings?";
        const params = new URLSearchParams();
        if (filterDateStart.value) params.append("date_start", filterDateStart.value);
        if (filterDateEnd.value) params.append("date_end", filterDateEnd.value);
        if (filterFloorSelect.value) params.append("andar", filterFloorSelect.value);
        
        const bookings = await fetchWithAuth(url + params.toString());

        if (bookings && bookings.length > 0) {
            bookingsTableBody.innerHTML = bookings.map(booking => `
                <tr>
                    <td>${new Date(booking.data + 'T00:00:00').toLocaleDateString('pt-BR')}</td>
                    <td>${booking.horario_desc}</td>
                    <td>${booking.andar_num}</td>
                    <td>${booking.lavanderia_identificador}</td>
                    <td>${booking.morador_nome}</td>
                    <td>${booking.morador_apto}</td>
                    <td>${booking.status_agendamento}</td>
                </tr>
            `).join("");
        } else if (bookings) {
            bookingsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Nenhum agendamento encontrado para os filtros aplicados.</td></tr>`;
        } else {
            bookingsTableBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Erro ao carregar agendamentos.</td></tr>`;
        }
    }

    async function loadLaundries() {
        laundriesTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Carregando lavanderias...</td></tr>`;
        const laundries = await fetchWithAuth("/api/admin/all_laundries");

        if (laundries && laundries.length > 0) {
            laundriesTableBody.innerHTML = laundries.map(laundry => `
                <tr>
                    <td>${laundry.andar_num}</td>
                    <td>${laundry.identificador}</td>
                    <td><span class="status-${laundry.status.toLowerCase()}">${laundry.status === 'ativa' ? 'Ativa' : 'Em Manutenção'}</span></td>
                    <td>
                        <button class="maintenance-btn ${laundry.status === 'ativa' ? 'deactivate' : 'activate'}" 
                                data-id="${laundry.id_lavanderia}" 
                                data-current-status="${laundry.status}">
                            ${laundry.status === 'ativa' ? 'Pôr em Manutenção' : 'Ativar Lavanderia'}
                        </button>
                    </td>
                </tr>
            `).join("");

            document.querySelectorAll(".maintenance-btn").forEach(button => {
                button.addEventListener("click", handleToggleMaintenance);
            });
        } else if (laundries) {
            laundriesTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Nenhuma lavanderia encontrada.</td></tr>`;
        } else {
             laundriesTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center;">Erro ao carregar lavanderias.</td></tr>`;
        }
    }

    async function handleToggleMaintenance(event) {
        const button = event.target;
        const laundryId = button.dataset.id;
        const currentStatus = button.dataset.currentStatus;
        const newStatus = currentStatus === "ativa" ? "manutencao" : "ativa";
        const actionText = newStatus === "ativa" ? "ativar" : "colocar em manutenção";

        if (confirm(`Tem certeza que deseja ${actionText} a lavanderia ${laundryId}?`)) {
            const result = await fetchWithAuth(`/api/admin/laundry/${laundryId}/status`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ status: newStatus }),
            });

            if (result) {
                alert(`Lavanderia ${result.lavanderia.id_lavanderia} foi ${newStatus === 'ativa' ? 'ativada' : 'colocada em manutenção'} com sucesso.`);
                loadLaundries(); // Recarrega a lista de lavanderias
                // Se o dashboard de agendamentos do usuário estivesse na mesma página, recarregaria também.
            } else {
                alert("Falha ao atualizar status da lavanderia.");
            }
        }
    }

    // Event Listeners
    if(applyFiltersBtn) {
        applyFiltersBtn.addEventListener("click", loadBookings);
    }

    // Initial Load
    loadFloors();
    loadBookings();
    loadLaundries();
});

