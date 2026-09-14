const API_URL = 'http://localhost:8000/api/v1';

const bookingForm = document.getElementById('bookingForm');
const serviceSelect = document.getElementById('bookingService');
const dateInput = document.getElementById('bookingDate');
const timeSelect = document.getElementById('bookingTime');
const nameInput = document.getElementById('bookingName');
const phoneInput = document.getElementById('bookingPhone');
const guestsInput = document.getElementById('bookingGuests');
const durationInput = document.getElementById('bookingDuration');
const commentInput = document.getElementById('bookingComment');
const messageEl = document.getElementById('bookingMessage');


async function loadServices() {
  try {
    const response = await fetch(`${API_URL}/services/`);

    if (!response.ok) {
      throw new Error('Failed to load services');
    }

    const services = await response.json();

    serviceSelect.innerHTML =
      '<option value="">Оберіть послугу</option>';

    services.forEach((service) => {
      const option = document.createElement('option');

      option.value = service.id;
      option.textContent =
        `${service.name} — ${service.price} грн`;

      option.dataset.minimumDuration =
        service.minimum_duration_hours;

      serviceSelect.appendChild(option);
    });
  } catch (error) {
    showMessage(
      'Не вдалося завантажити послуги.',
      true
    );
  }
}


async function loadAvailability() {
  const serviceId = serviceSelect.value;
  const date = dateInput.value;

  if (!serviceId || !date) {
    return;
  }

  timeSelect.disabled = true;
  timeSelect.innerHTML =
    '<option value="">Завантаження...</option>';

  try {
    const response = await fetch(
      `${API_URL}/services/${serviceId}/availability?date=${date}`
    );

    if (!response.ok) {
      throw new Error('Failed to load availability');
    }

    const slots = await response.json();

    timeSelect.innerHTML = '';

    if (slots.length === 0) {
      timeSelect.innerHTML =
        '<option value="">Вільного часу немає</option>';

      return;
    }

    timeSelect.innerHTML =
      '<option value="">Оберіть час</option>';

    slots.forEach((slot) => {
      const option = document.createElement('option');

      option.value = slot;

      const slotDate = new Date(slot);

      option.textContent =
        slotDate.toLocaleTimeString('uk-UA', {
          hour: '2-digit',
          minute: '2-digit',
        });

      timeSelect.appendChild(option);
    });

    timeSelect.disabled = false;
  } catch (error) {
    timeSelect.innerHTML =
      '<option value="">Помилка завантаження</option>';

    showMessage(
      'Не вдалося отримати вільний час.',
      true
    );
  }
}


function showMessage(message, isError = false) {
  messageEl.textContent = message;
  messageEl.classList.toggle(
    'is-error',
    isError
  );
}


serviceSelect.addEventListener('change', () => {
  const selectedOption =
    serviceSelect.options[serviceSelect.selectedIndex];

  if (selectedOption?.dataset.minimumDuration) {
    durationInput.value =
      selectedOption.dataset.minimumDuration;
  }

  loadAvailability();
});


dateInput.addEventListener(
  'change',
  loadAvailability
);


bookingForm.addEventListener(
  'submit',
  async (event) => {
    event.preventDefault();

    showMessage('Створюємо бронювання...');

    const payload = {
      service_id: Number(serviceSelect.value),
      customer_name: nameInput.value.trim(),
      customer_phone: phoneInput.value.trim(),
      starts_at: timeSelect.value,
      guests: Number(guestsInput.value),
      comment: commentInput.value.trim() || null,
      duration_hours: durationInput.value
        ? Number(durationInput.value)
        : null,
    };

    try {
      const response = await fetch(
        `${API_URL}/bookings/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || 'Booking failed'
        );
      }

      showMessage(
        'Бронювання створено. Очікуйте підтвердження.'
      );

      bookingForm.reset();

      timeSelect.disabled = true;
      timeSelect.innerHTML =
        '<option value="">Спочатку оберіть дату</option>';

    } catch (error) {
      showMessage(
        error.message,
        true
      );
    }
  }
);


loadServices();