document.addEventListener('DOMContentLoaded', () => {
    const userFloorSpan = document.getElementById('user-floor');
    const userApartmentSpan = document.getElementById('user-apartment');
    const scheduleDateInput = document.getElementById('schedule-date');
    const selectedDateDisplay = document.getElementById('selected-date-display');
    const timeSlotsLaundry1 = document.getElementById('time-slots-laundry-1');
    const timeSlotsLaundry2 = document.getElementById('time-slots-laundry-2');
    const myBookingsList = document.getElementById('my-bookings-list');

    // Horários fixos definidos
    const timeSlotsDefinition = [
        { id: '07-11', label: '07:00 - 11:00' },
        { id: '11-15', label: '11:00 - 15:00' },
        { id: '15-19', label: '15:00 - 19:00' },
        { id: '19-23', label: '19:00 - 23:00' },
    ];

    // --- Simulação de Dados (substituir por chamadas de API reais) ---
    const mockUser = {
        floor: 5, // Exemplo
        apartment: '502' // Exemplo
    };

    // Formato: { 'YYYY-MM-DD': { 'laundry_id': ['time_slot_id', ...] } }
    let mockBookings = {
        // Exemplo: '2025-05-20': { '1': ['07-11'], '2': ['11-15'] }
    };

    let myMockUserBookings = [
        // { date: '2025-05-18', time: '15:00-19:00', laundry: 'Lavanderia 1', id: 'booking1' },
    ];
    // --- Fim da Simulação de Dados ---

    function initialize() {
        // Define a data mínima como hoje
        const today = new Date().toISOString().split('T')[0];
        scheduleDateInput.setAttribute('min', today);
        scheduleDateInput.value = today; // Define a data padrão como hoje

        updateUserInfo();
        updateSelectedDateDisplay(today);
        loadAvailableSlots(today);
        loadMyBookings();

        scheduleDateInput.addEventListener('change', (event) => {
            const selectedDate = event.target.value;
            updateSelectedDateDisplay(selectedDate);
            loadAvailableSlots(selectedDate);
        });
    }

    function updateUserInfo() {
        // TODO: Obter dados do usuário via API após login
        userFloorSpan.textContent = mockUser.floor;
        userApartmentSpan.textContent = mockUser.apartment;
    }

    function updateSelectedDateDisplay(date) {
        if (date) {
            const [year, month, day] = date.split('-');
            selectedDateDisplay.textContent = `${day}/${month}/${year}`;
        } else {
            selectedDateDisplay.textContent = 'Data não selecionada';
        }
    }

    function renderTimeSlots(laundryId, containerElement, date) {
        containerElement.innerHTML = ''; // Limpa horários anteriores
        const bookingsForDateAndLaundry = mockBookings[date]?.[laundryId] || [];

        timeSlotsDefinition.forEach(slot => {
            const slotDiv = document.createElement('div');
            slotDiv.classList.add('time-slot');
            slotDiv.textContent = slot.label;
            slotDiv.dataset.timeSlotId = slot.id;
            slotDiv.dataset.laundryId = laundryId;
            slotDiv.dataset.date = date;

            if (bookingsForDateAndLaundry.includes(slot.id)) {
                slotDiv.classList.add('booked');
                slotDiv.title = 'Horário Ocupado';
            } else {
                slotDiv.classList.add('available');
                slotDiv.title = 'Clique para agendar';
                slotDiv.addEventListener('click', handleSlotClick);
            }
            containerElement.appendChild(slotDiv);
        });
    }

    function loadAvailableSlots(date) {
        // TODO: Obter horários ocupados da API para a data selecionada e andar do usuário
        // Por enquanto, usa mockBookings
        renderTimeSlots('1', timeSlotsLaundry1, date); // Lavanderia 1 do andar do usuário
        renderTimeSlots('2', timeSlotsLaundry2, date); // Lavanderia 2 do andar do usuário
    }

    function handleSlotClick(event) {
        const slotDiv = event.currentTarget;
        if (slotDiv.classList.contains('booked')) {
            alert('Este horário já está ocupado.');
            return;
        }

        const laundryId = slotDiv.dataset.laundryId;
        const timeSlotId = slotDiv.dataset.timeSlotId;
        const date = slotDiv.dataset.date;
        const laundryName = laundryId === '1' ? 'Lavanderia 1' : 'Lavanderia 2';

        if (confirm(`Confirmar agendamento para ${laundryName} no dia ${selectedDateDisplay.textContent} (${slotDiv.textContent})?`)) {
            // TODO: Enviar solicitação de agendamento para a API
            // Simulação de sucesso:
            console.log(`Agendamento solicitado: Lavanderia ${laundryId}, Horário ${timeSlotId}, Data ${date}`);

            // Atualiza mockBookings (simulação)
            if (!mockBookings[date]) mockBookings[date] = {};
            if (!mockBookings[date][laundryId]) mockBookings[date][laundryId] = [];
            mockBookings[date][laundryId].push(timeSlotId);

            // Adiciona ao mock de meus agendamentos
            myMockUserBookings.push({
                date: date,
                time: slotDiv.textContent,
                laundry: laundryName,
                id: `booking-${Date.now()}` // ID único para simulação
            });

            // Recarrega os slots e meus agendamentos
            loadAvailableSlots(date);
            loadMyBookings();
            alert('Agendamento realizado com sucesso! (Simulação)');
        } else {
            console.log('Agendamento cancelado pelo usuário.');
        }
    }

    function loadMyBookings() {
        // TODO: Obter meus agendamentos da API
        myBookingsList.innerHTML = ''; // Limpa lista anterior

        if (myMockUserBookings.length === 0) {
            const li = document.createElement('li');
            li.classList.add('no-bookings');
            li.textContent = 'Nenhum agendamento encontrado.';
            myBookingsList.appendChild(li);
            return;
        }

        myMockUserBookings.sort((a, b) => new Date(a.date + ' ' + a.time.split(' - ')[0]) - new Date(b.date + ' ' + b.time.split(' - ')[0]));

        myMockUserBookings.forEach(booking => {
            const li = document.createElement('li');
            const [year, month, day] = booking.date.split('-');
            li.innerHTML = `
                <span>${day}/${month}/${year} - ${booking.time} (${booking.laundry})</span>
                <button class="cancel-booking-btn" data-booking-id="${booking.id}">Cancelar</button>
            `;
            const cancelButton = li.querySelector('.cancel-booking-btn');
            cancelButton.addEventListener('click', handleCancelBooking);
            myBookingsList.appendChild(li);
        });
    }

    function handleCancelBooking(event) {
        const bookingIdToCancel = event.target.dataset.bookingId;
        const bookingToCancel = myMockUserBookings.find(b => b.id === bookingIdToCancel);

        if (!bookingToCancel) {
            alert('Erro ao encontrar agendamento para cancelar.');
            return;
        }

        if (confirm(`Tem certeza que deseja cancelar o agendamento: ${bookingToCancel.laundry} em ${bookingToCancel.date} (${bookingToCancel.time})?`)) {
            // TODO: Enviar solicitação de cancelamento para a API
            console.log(`Cancelamento solicitado para booking ID: ${bookingIdToCancel}`);

            // Remove do mockBookings (simulação)
            const date = bookingToCancel.date;
            const laundryId = bookingToCancel.laundry.includes('1') ? '1' : '2';
            const timeSlotLabel = bookingToCancel.time;
            const timeSlotIdToCancel = timeSlotsDefinition.find(ts => ts.label === timeSlotLabel)?.id;

            if (mockBookings[date] && mockBookings[date][laundryId] && timeSlotIdToCancel) {
                mockBookings[date][laundryId] = mockBookings[date][laundryId].filter(id => id !== timeSlotIdToCancel);
                if (mockBookings[date][laundryId].length === 0) delete mockBookings[date][laundryId];
                if (Object.keys(mockBookings[date]).length === 0) delete mockBookings[date];
            }

            // Remove do mock de meus agendamentos
            myMockUserBookings = myMockUserBookings.filter(b => b.id !== bookingIdToCancel);

            // Recarrega os slots e meus agendamentos
            loadAvailableSlots(scheduleDateInput.value);
            loadMyBookings();
            alert('Agendamento cancelado com sucesso! (Simulação)');
        }
    }

    // Inicia a aplicação
    initialize();
});

