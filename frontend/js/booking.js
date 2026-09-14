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

const submitButton = bookingForm.querySelector(
  'button[type="submit"]'
);


function showMessage(message, isError = false) {
  messageEl.textContent = message;

  messageEl.classList.toggle(
    'is-error',
    isError
  );
}


function setMinimumBookingDate() {
  const today = new Date();

  const year = today.getFullYear();

  const month = String(
    today.getMonth() + 1
  ).padStart(2, '0');

  const day = String(
    today.getDate()
  ).padStart(2, '0');

  dateInput.min = `${year}-${month}-${day}`;
}


async function loadServices() {
  try {
    const response = await fetch(
      `${API_URL}/services/`
    );

    if (!response.ok) {
      throw new Error(
        'Failed to load services'
      );
    }

    const services = await response.json();

    serviceSelect.innerHTML =
      '<option value="">Оберіть послугу</option>';

    services.forEach((service) => {
      const option =
        document.createElement('option');

      option.value = service.id;

      option.textContent =
        `${service.name} — ${service.price} грн`;

      option.dataset.minimumDuration =
        service.minimum_duration_hours;

      option.dataset.serviceName =
        service.name;

      serviceSelect.appendChild(option);
    });

    const params =
      new URLSearchParams(window.location.search);

    const requestedService =
      params.get('service');

    if (requestedService) {
      const matchingOption =
        Array.from(serviceSelect.options)
          .find(
            (option) =>
              option.dataset.serviceName ===
              requestedService
          );

      if (matchingOption) {
        serviceSelect.value =
          matchingOption.value;

        serviceSelect.dispatchEvent(
          new Event('change')
        );
      }
    }

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
    timeSelect.disabled = true;

    timeSelect.innerHTML =
      '<option value="">Спочатку оберіть послугу та дату</option>';

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
      throw new Error(
        'Failed to load availability'
      );
    }

    const slots = await response.json();

    if (slots.length === 0) {
      timeSelect.innerHTML =
        '<option value="">Вільного часу немає</option>';

      return;
    }

    timeSelect.innerHTML =
      '<option value="">Оберіть час</option>';

    slots.forEach((slot) => {
      const option =
        document.createElement('option');

      option.value = slot;

      const slotDate = new Date(slot);

      option.textContent =
        slotDate.toLocaleTimeString(
          'uk-UA',
          {
            hour: '2-digit',
            minute: '2-digit',
          }
        );

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


serviceSelect.addEventListener(
  'change',
  () => {
    const selectedOption =
      serviceSelect.options[
        serviceSelect.selectedIndex
      ];

    const minimumDuration =
      selectedOption?.dataset.minimumDuration;

    if (minimumDuration) {
      durationInput.value =
        minimumDuration;

      durationInput.min =
        minimumDuration;
    } else {
      durationInput.value = '';
      durationInput.min = '1';
    }

    loadAvailability();
  }
);


dateInput.addEventListener(
  'change',
  loadAvailability
);


bookingForm.addEventListener(
  'submit',
  async (event) => {
    event.preventDefault();

    showMessage(
      'Створюємо бронювання...'
    );

    submitButton.disabled = true;
    submitButton.textContent =
      'Відправляємо...';

    const payload = {
      service_id:
        Number(serviceSelect.value),

      customer_name:
        nameInput.value.trim(),

      customer_phone:
        phoneInput.value.trim(),

      starts_at:
        timeSelect.value,

      guests:
        Number(guestsInput.value),

      comment:
        commentInput.value.trim() || null,

      duration_hours:
        durationInput.value
          ? Number(durationInput.value)
          : null,
    };

    try {
      const response = await fetch(
        `${API_URL}/bookings/`,
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify(payload),
        }
      );

      const data =
        await response.json();

      if (!response.ok) {
        let message =
          'Не вдалося створити бронювання.';

        if (response.status === 400) {
          message =
            data.detail ||
            'Некоректні дані бронювання.';
        }

        if (response.status === 409) {
          message =
            'Цей час уже зайнятий. Оберіть інший слот.';
        }

        if (response.status === 422) {
          message =
            'Перевірте правильність заповнення форми.';
        }

        if (response.status === 429) {
          message =
            'Забагато спроб. Спробуйте трохи пізніше.';
        }

        throw new Error(message);
      }

      showMessage(
        'Бронювання створено. Очікуйте підтвердження.'
      );

      bookingForm.reset();

      durationInput.min = '1';

      timeSelect.disabled = true;

      timeSelect.innerHTML =
        '<option value="">Спочатку оберіть послугу та дату</option>';

    } catch (error) {
      showMessage(
        error.message,
        true
      );

    } finally {
      submitButton.disabled = false;

      submitButton.textContent =
        'Підтвердити бронювання';
    }
  }
);


setMinimumBookingDate();
loadServices();