const API_URL = '/api/v1';

const bookingForm =
  document.getElementById('bookingForm');

const serviceSelect =
  document.getElementById('bookingService');

const dateInput =
  document.getElementById('bookingDate');

const timeSelect =
  document.getElementById('bookingTime');

const durationInput =
  document.getElementById('bookingDuration');

const checkInInput =
  document.getElementById('bookingCheckIn');

const checkOutInput =
  document.getElementById('bookingCheckOut');

const nameInput =
  document.getElementById('bookingName');

const phoneInput =
  document.getElementById('bookingPhone');

const guestsInput =
  document.getElementById('bookingGuests');

const commentInput =
  document.getElementById('bookingComment');

const messageEl =
  document.getElementById('bookingMessage');

const submitButton =
  bookingForm.querySelector(
    'button[type="submit"]'
  );


const hourlyDateGroup =
  document.getElementById('hourlyDateGroup');

const hourlyTimeGroup =
  document.getElementById('hourlyTimeGroup');

const hourlyDurationGroup =
  document.getElementById(
    'hourlyDurationGroup'
  );

const dailyCheckInGroup =
  document.getElementById(
    'dailyCheckInGroup'
  );

const dailyCheckOutGroup =
  document.getElementById(
    'dailyCheckOutGroup'
  );

const phoneOnlyNotice =
  document.getElementById(
    'phoneOnlyNotice'
  );

const customerDivider =
  document.getElementById(
    'customerDivider'
  );

const nameGroup =
  document.getElementById('nameGroup');

const phoneGroup =
  document.getElementById('phoneGroup');

const guestsGroup =
  document.getElementById('guestsGroup');

const commentGroup =
  document.getElementById('commentGroup');

const submitGroup =
  document.getElementById('submitGroup');


let selectedService = null;


function showMessage(
  message,
  isError = false
) {
  messageEl.textContent = message;

  messageEl.classList.toggle(
    'is-error',
    isError
  );
}


function formatDateForInput(date) {
  const year = date.getFullYear();

  const month = String(
    date.getMonth() + 1
  ).padStart(2, '0');

  const day = String(
    date.getDate()
  ).padStart(2, '0');

  return `${year}-${month}-${day}`;
}


function addDays(
  dateString,
  days
) {
  const [
    year,
    month,
    day
  ] = dateString
    .split('-')
    .map(Number);

  const date = new Date(
    year,
    month - 1,
    day
  );

  date.setDate(
    date.getDate() + days
  );

  return formatDateForInput(date);
}


function setMinimumBookingDates() {
  const today =
    formatDateForInput(
      new Date()
    );

  dateInput.min = today;

  checkInInput.min = today;
}


function hideAllConditionalFields() {
  hourlyDateGroup.hidden = true;
  hourlyTimeGroup.hidden = true;
  hourlyDurationGroup.hidden = true;

  dailyCheckInGroup.hidden = true;
  dailyCheckOutGroup.hidden = true;

  phoneOnlyNotice.hidden = true;

  customerDivider.hidden = true;

  nameGroup.hidden = true;
  phoneGroup.hidden = true;
  guestsGroup.hidden = true;
  commentGroup.hidden = true;

  submitGroup.hidden = true;


  dateInput.required = false;
  timeSelect.required = false;
  durationInput.required = false;

  checkInInput.required = false;
  checkOutInput.required = false;

  nameInput.required = false;
  phoneInput.required = false;
  guestsInput.required = false;
}


function showCustomerFields() {
  customerDivider.hidden = false;

  nameGroup.hidden = false;
  phoneGroup.hidden = false;
  guestsGroup.hidden = false;
  commentGroup.hidden = false;

  submitGroup.hidden = false;

  nameInput.required = true;
  phoneInput.required = true;
  guestsInput.required = true;
}


function resetAvailability() {
  timeSelect.disabled = true;

  timeSelect.innerHTML =
    '<option value="">Спочатку оберіть дату</option>';
}


function configureHourlyService() {
  hourlyDateGroup.hidden = false;
  hourlyTimeGroup.hidden = false;
  hourlyDurationGroup.hidden = false;

  dateInput.required = true;
  timeSelect.required = true;
  durationInput.required = true;

  const minimumDuration =
    selectedService
      .minimum_duration_hours;

  durationInput.min =
    minimumDuration || 1;

  durationInput.value =
    minimumDuration || '';

  showCustomerFields();

  resetAvailability();

  if (dateInput.value) {
    loadAvailability();
  }
}


function updateCheckOutMinimum() {
  if (!selectedService) {
    return;
  }

  const minimumDays =
    selectedService
      .minimum_duration_days || 1;

  if (!checkInInput.value) {
    checkOutInput.min =
      addDays(
        formatDateForInput(new Date()),
        minimumDays
      );

    return;
  }

  const minimumCheckOut =
    addDays(
      checkInInput.value,
      minimumDays
    );

  checkOutInput.min =
    minimumCheckOut;

  if (
    checkOutInput.value &&
    checkOutInput.value <
      minimumCheckOut
  ) {
    checkOutInput.value =
      minimumCheckOut;
  }
}


function configureDailyService() {
  dailyCheckInGroup.hidden = false;
  dailyCheckOutGroup.hidden = false;

  checkInInput.required = true;
  checkOutInput.required = true;

  updateCheckOutMinimum();

  showCustomerFields();
}


function configurePhoneOnlyService() {
  phoneOnlyNotice.hidden = false;
}


function configureServiceForm() {
  hideAllConditionalFields();

  resetAvailability();

  showMessage('');

  const selectedOption =
    serviceSelect.options[
      serviceSelect.selectedIndex
    ];

  if (
    !selectedOption ||
    !selectedOption.value
  ) {
    selectedService = null;
    return;
  }

  selectedService = {
    id:
      Number(
        selectedOption.value
      ),

    name:
      selectedOption
        .dataset.serviceName,

    booking_type:
      selectedOption
        .dataset.bookingType,

    minimum_duration_hours:
      selectedOption
        .dataset.minimumDurationHours
        ? Number(
            selectedOption
              .dataset.minimumDurationHours
          )
        : null,

    minimum_duration_days:
      selectedOption
        .dataset.minimumDurationDays
        ? Number(
            selectedOption
              .dataset.minimumDurationDays
          )
        : null,
  };


  if (
    selectedService.booking_type
    === 'hourly'
  ) {
    configureHourlyService();
    return;
  }


  if (
    selectedService.booking_type
    === 'daily'
  ) {
    configureDailyService();
    return;
  }


  if (
    selectedService.booking_type
    === 'phone_only'
  ) {
    configurePhoneOnlyService();
  }
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

    const services =
      await response.json();

    serviceSelect.innerHTML =
        '<option value="" disabled selected hidden>Оберіть послугу</option>';

    services.forEach(
      (service) => {
        const option =
          document.createElement(
            'option'
          );

        option.value =
          service.id;

        option.textContent =
          service.name;

        option.dataset.serviceName =
          service.name;

        option.dataset.bookingType =
          service.booking_type;

        option.dataset.minimumDurationHours =
          service.minimum_duration_hours
          ?? '';

        option.dataset.minimumDurationDays =
          service.minimum_duration_days
          ?? '';

        serviceSelect.appendChild(
          option
        );
      }
    );


    const params =
      new URLSearchParams(
        window.location.search
      );

    const requestedService =
      params.get('service');

    if (requestedService) {
      const matchingOption =
        Array
          .from(
            serviceSelect.options
          )
          .find(
            (option) =>
              option.dataset
                .serviceName
              === requestedService
          );

      if (matchingOption) {
        serviceSelect.value =
          matchingOption.value;

        configureServiceForm();
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
  if (
    !selectedService ||
    selectedService.booking_type
      !== 'hourly'
  ) {
    return;
  }

  const serviceId =
    selectedService.id;

  const date =
    dateInput.value;


  if (!serviceId || !date) {
    resetAvailability();
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

    const slots =
      await response.json();


    if (slots.length === 0) {
      timeSelect.innerHTML =
        '<option value="">Вільного часу немає</option>';

      return;
    }


    timeSelect.innerHTML =
      '<option value="">Оберіть час</option>';


    slots.forEach((slot) => {
      const option =
        document.createElement(
          'option'
        );

      option.value = slot;

      const slotDate =
        new Date(slot);

      option.textContent =
        slotDate.toLocaleTimeString(
          'uk-UA',
          {
            hour: '2-digit',
            minute: '2-digit',
            timeZone:
              'Europe/Kyiv',
          }
        );

      timeSelect.appendChild(
        option
      );
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
  configureServiceForm
);


dateInput.addEventListener(
  'change',
  loadAvailability
);


checkInInput.addEventListener(
  'change',
  () => {
    updateCheckOutMinimum();
  }
);


bookingForm.addEventListener(
  'submit',
  async (event) => {
    event.preventDefault();


    if (!selectedService) {
      showMessage(
        'Оберіть послугу.',
        true
      );

      return;
    }


    if (
      selectedService.booking_type
      === 'phone_only'
    ) {
      return;
    }


    showMessage(
      'Надсилаємо заявку...'
    );


    submitButton.disabled = true;

    submitButton.textContent =
      'Надсилаємо...';


    const payload = {
      service_id:
        selectedService.id,

      customer_name:
        nameInput.value.trim(),

      customer_phone:
        phoneInput.value.trim(),

      guests:
        Number(
          guestsInput.value
        ),

      comment:
        commentInput.value
          .trim()
        || null,
    };


    if (
      selectedService.booking_type
      === 'hourly'
    ) {
      payload.starts_at =
        timeSelect.value;

      payload.duration_hours =
        Number(
          durationInput.value
        );
    }


    if (
      selectedService.booking_type
      === 'daily'
    ) {
      payload.check_in_date =
        checkInInput.value;

      payload.check_out_date =
        checkOutInput.value;
    }


    try {
      const response = await fetch(
        `${API_URL}/bookings/`,
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json',
          },

          body:
            JSON.stringify(
              payload
            ),
        }
      );


      let data = {};

      try {
        data =
          await response.json();
      } catch {
        data = {};
      }


      if (!response.ok) {
        let message =
          'Не вдалося створити бронювання.';


        if (
          response.status === 400
        ) {
          message =
            data.detail ||
            'Некоректні дані бронювання.';
        }


        if (
          response.status === 409
        ) {
          message =
            selectedService
              .booking_type
            === 'daily'
              ? 'Ці дати вже зайняті. Оберіть інші.'
              : 'Цей час уже зайнятий. Оберіть інший.';
        }


        if (
          response.status === 422
        ) {
          message =
            'Перевірте правильність заповнення форми.';
        }


        if (
          response.status === 429
        ) {
          message =
            'Забагато спроб. Спробуйте трохи пізніше.';
        }


        throw new Error(message);
      }


      bookingForm.reset();

      selectedService = null;

      hideAllConditionalFields();

      resetAvailability();

      setMinimumBookingDates();


      showMessage(
        'Заявку на бронювання створено. Очікуйте підтвердження.'
      );

    } catch (error) {
      showMessage(
        error.message ||
        'Не вдалося створити бронювання.',
        true
      );

    } finally {
      submitButton.disabled = false;

      submitButton.textContent =
        'Надіслати заявку';
    }
  }
);


setMinimumBookingDates();

hideAllConditionalFields();

loadServices();