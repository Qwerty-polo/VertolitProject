const API_URL = '/api/v1';


const loginSection =
  document.getElementById('adminLogin');

const dashboard =
  document.getElementById('adminDashboard');

const loginForm =
  document.getElementById('adminLoginForm');

const passwordInput =
  document.getElementById('adminPassword');

const loginButton =
  document.getElementById('adminLoginButton');

const loginMessage =
  document.getElementById('loginMessage');

const logoutButton =
  document.getElementById('adminLogout');


const tableBody =
  document.getElementById('bookingsTableBody');

const adminMessage =
  document.getElementById('adminMessage');

const emptyState =
  document.getElementById('adminEmpty');

const refreshButton =
  document.getElementById('refreshBookings');

const statusFilter =
  document.getElementById('statusFilter');

const dateFilter =
  document.getElementById('dateFilter');

const bookingSearch =
  document.getElementById('bookingSearch');

const pendingCount =
  document.getElementById('pendingCount');

const confirmedCount =
  document.getElementById('confirmedCount');

const completedCount =
  document.getElementById('completedCount');

const cancelledCount =
  document.getElementById('cancelledCount');


let bookings = [];

let services = new Map();


const STATUS_LABELS = {
  pending: 'Очікує',
  confirmed: 'Підтверджено',
  cancelled: 'Скасовано',
  completed: 'Завершено',
};


function showLoginMessage(
  message,
  isError = false
) {
  loginMessage.textContent = message;

  loginMessage.classList.toggle(
    'is-error',
    isError
  );
}


function showAdminMessage(
  message,
  isError = false
) {
  adminMessage.textContent = message;

  adminMessage.classList.toggle(
    'is-error',
    isError
  );
}


function showLogin() {
  loginSection.hidden = false;
  dashboard.hidden = true;

  loginSection.style.display = 'flex';
  dashboard.style.display = 'none';

  passwordInput.value = '';

  setTimeout(() => {
    passwordInput.focus();
  }, 0);
}


function showDashboard() {
  loginSection.hidden = true;
  dashboard.hidden = false;

  loginSection.style.display = 'none';
  dashboard.style.display = 'block';
}


async function apiFetch(
  path,
  options = {}
) {
  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,

      credentials: 'include',

      headers: {
        ...(options.headers || {}),
      },
    }
  );

  if (response.status === 401) {
    showLogin();

    throw new Error(
      'Сесія завершилась. Увійдіть ще раз.'
    );
  }

  return response;
}


async function checkAdminSession() {
  try {
    const response = await fetch(
      `${API_URL}/admin/session`,
      {
        credentials: 'include',
      }
    );

    if (!response.ok) {
      showLogin();
      return;
    }

    showDashboard();

    await loadAdminData();

  } catch (error) {
    showLogin();

    showLoginMessage(
      'Не вдалося підключитися до сервера.',
      true
    );
  }
}


loginForm.addEventListener(
  'submit',
  async (event) => {
    event.preventDefault();

    const password =
      passwordInput.value;

    if (!password) {
      return;
    }

    loginButton.disabled = true;

    loginButton.textContent =
      'Входимо...';

    showLoginMessage(
      'Перевіряємо пароль...'
    );

    try {
      const response = await fetch(
        `${API_URL}/admin/login`,
        {
          method: 'POST',

          credentials: 'include',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify({
            password,
          }),
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
        if (response.status === 401) {
          throw new Error(
            'Неправильний пароль.'
          );
        }

        if (response.status === 429) {
          throw new Error(
            'Забагато спроб. Спробуйте пізніше.'
          );
        }
          if (response.status === 503) {
              throw new Error(
                  'Сервіс входу тимчасово ' +
                  'недоступний. Спробуйте пізніше.'
              );
          }

        throw new Error(
          data.detail ||
          'Не вдалося увійти.'
        );
      }

      passwordInput.value = '';

      showLoginMessage('');

      showDashboard();

      await loadAdminData();

    } catch (error) {
      showLoginMessage(
        error.message ||
        'Не вдалося увійти.',
        true
      );

    } finally {
      loginButton.disabled = false;

      loginButton.textContent =
        'Увійти';
    }
  }
);


logoutButton.addEventListener(
  'click',
  async () => {
    logoutButton.disabled = true;

    try {
      await fetch(
        `${API_URL}/admin/logout`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

    } finally {
      logoutButton.disabled = false;

      showLogin();

      showLoginMessage(
        'Ви вийшли з адмін-панелі.'
      );
    }
  }
);


function formatBookingDate(value) {
  const date =
    new Date(value);

  return new Intl.DateTimeFormat(
    'uk-UA',
    {
      timeZone: 'Europe/Kyiv',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }
  ).format(date);
}


function getKyivDateString(value) {
  const parts =
    new Intl.DateTimeFormat(
      'en-CA',
      {
        timeZone: 'Europe/Kyiv',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      }
    ).formatToParts(
      new Date(value)
    );

  const values = {};

  parts.forEach((part) => {
    values[part.type] =
      part.value;
  });

  return (
    `${values.year}-` +
    `${values.month}-` +
    `${values.day}`
  );
}


function getDurationHours(
  booking
) {
  const start =
    new Date(booking.starts_at);

  const end =
    new Date(booking.ends_at);

  const milliseconds =
    end.getTime() -
    start.getTime();

  return Math.round(
    milliseconds /
    1000 /
    60 /
    60
  );
}


function getDurationDays(
  booking
) {
  const start =
    new Date(booking.starts_at);

  const end =
    new Date(booking.ends_at);

  const milliseconds =
    end.getTime() -
    start.getTime();

  return Math.round(
    milliseconds /
    1000 /
    60 /
    60 /
    24
  );
}


function formatBookingDateOnly(
  value
) {
  return new Intl.DateTimeFormat(
    'uk-UA',
    {
      timeZone: 'Europe/Kyiv',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }
  ).format(
    new Date(value)
  );
}


function formatBookingPeriod(
  booking
) {
  const service =
    getService(
      booking.service_id
    );

  if (
    service?.booking_type
    === 'daily'
  ) {
    return (
      `${formatBookingDateOnly(
        booking.starts_at
      )} → ` +
      `${formatBookingDateOnly(
        booking.ends_at
      )}`
    );
  }

  return formatBookingDate(
    booking.starts_at
  );
}


function formatBookingDuration(
  booking
) {
  const service =
    getService(
      booking.service_id
    );

  if (
    service?.booking_type
    === 'daily'
  ) {
    const days =
      getDurationDays(booking);

    if (days === 1) {
      return '1 ніч';
    }

    return `${days} ночі`;
  }

  return `${getDurationHours(
    booking
  )} год.`;
}


function getService(
  serviceId
) {
  return (
    services.get(
      Number(serviceId)
    ) || null
  );
}


function getServiceName(
  serviceId
) {
  const service =
    getService(serviceId);

  return (
    service?.name ||
    `Послуга #${serviceId}`
  );
}


function updateStats() {
  pendingCount.textContent =
    bookings.filter(
      (booking) =>
        booking.status === 'pending'
    ).length;

  confirmedCount.textContent =
    bookings.filter(
      (booking) =>
        booking.status ===
        'confirmed'
    ).length;

  completedCount.textContent =
    bookings.filter(
      (booking) =>
        booking.status ===
        'completed'
    ).length;

  cancelledCount.textContent =
    bookings.filter(
      (booking) =>
        booking.status ===
        'cancelled'
    ).length;
}


function getFilteredBookings() {
  const status =
    statusFilter.value;

  const date =
    dateFilter.value;

  const query =
    bookingSearch.value
      .trim()
      .toLowerCase();

  return bookings
    .filter((booking) => {
      if (
        status &&
        booking.status !== status
      ) {
        return false;
      }

      if (
        date &&
        getKyivDateString(
          booking.starts_at
        ) !== date
      ) {
        return false;
      }

      if (query) {
        const serviceName =
          getServiceName(
            booking.service_id
          ).toLowerCase();

        const haystack = [
          booking.customer_name,
          booking.customer_phone,
          serviceName,
          String(booking.id),
        ]
          .join(' ')
          .toLowerCase();

        if (
          !haystack.includes(query)
        ) {
          return false;
        }
      }

      return true;
    })
    .sort((a, b) => {
      const priority = {
        pending: 0,
        confirmed: 1,
        completed: 2,
        cancelled: 3,
      };

      const difference =
        priority[a.status] -
        priority[b.status];

      if (difference !== 0) {
        return difference;
      }

      return (
        new Date(a.starts_at) -
        new Date(b.starts_at)
      );
    });
}


function createActionButton(
  label,
  className,
  bookingId,
  newStatus
) {
  const button =
    document.createElement(
      'button'
    );

  button.type = 'button';

  button.className =
    `admin-action ${className}`;

  button.textContent =
    label;

  button.addEventListener(
    'click',
    () => {
      updateBookingStatus(
        bookingId,
        newStatus,
        button
      );
    }
  );

  return button;
}


function renderActions(
  booking
) {
  const container =
    document.createElement(
      'div'
    );

  container.className =
    'admin-actions';

  if (
    booking.status ===
    'pending'
  ) {
    container.appendChild(
      createActionButton(
        'Підтвердити',
        'admin-action--confirm',
        booking.id,
        'confirmed'
      )
    );

    container.appendChild(
      createActionButton(
        'Скасувати',
        'admin-action--cancel',
        booking.id,
        'cancelled'
      )
    );
  }


  if (
    booking.status ===
    'confirmed'
  ) {
    container.appendChild(
      createActionButton(
        'Завершити',
        'admin-action--complete',
        booking.id,
        'completed'
      )
    );

    container.appendChild(
      createActionButton(
        'Скасувати',
        'admin-action--cancel',
        booking.id,
        'cancelled'
      )
    );
  }


  if (
    booking.status ===
      'cancelled' ||
    booking.status ===
      'completed'
  ) {
    const text =
      document.createElement(
        'span'
      );

    text.textContent = '—';

    container.appendChild(
      text
    );
  }

  return container;
}


function renderBookings() {
  const filtered =
    getFilteredBookings();

  tableBody.innerHTML = '';

  emptyState.hidden =
    filtered.length !== 0;

  filtered.forEach(
    (booking) => {
      const row =
        document.createElement(
          'tr'
        );


      const idCell =
        document.createElement(
          'td'
        );

      idCell.textContent =
        `#${booking.id}`;


      const serviceCell =
        document.createElement(
          'td'
        );

      serviceCell.textContent =
        getServiceName(
          booking.service_id
        );


      const clientCell =
        document.createElement(
          'td'
        );

      const client =
        document.createElement(
          'div'
        );

      client.className =
        'admin-client';


      const clientName =
        document.createElement(
          'strong'
        );

      clientName.textContent =
        booking.customer_name;


      const phone =
        document.createElement(
          'a'
        );

      phone.href =
        `tel:${booking.customer_phone}`;

      phone.textContent =
        booking.customer_phone;


      client.append(
        clientName,
        phone
      );

      clientCell.appendChild(
        client
      );


      const dateCell =
        document.createElement(
          'td'
        );

        dateCell.textContent =
            formatBookingPeriod(
                booking
            );


      const guestsCell =
        document.createElement(
          'td'
        );

      guestsCell.textContent =
        booking.guests;


      const durationCell =
        document.createElement(
          'td'
        );

        durationCell.textContent =
            formatBookingDuration(
                booking
            );


      const statusCell =
        document.createElement(
          'td'
        );

      const statusBadge =
        document.createElement(
          'span'
        );

      statusBadge.className =
        `admin-status ` +
        `admin-status--` +
        `${booking.status}`;

      statusBadge.textContent =
        STATUS_LABELS[
          booking.status
        ] ||
        booking.status;

      statusCell.appendChild(
        statusBadge
      );


      const actionsCell =
        document.createElement(
          'td'
        );

      actionsCell.appendChild(
        renderActions(booking)
      );


      row.append(
        idCell,
        serviceCell,
        clientCell,
        dateCell,
        guestsCell,
        durationCell,
        statusCell,
        actionsCell
      );

      tableBody.appendChild(
        row
      );
    }
  );
}


async function loadServices() {
  const response =
    await fetch(
      `${API_URL}/services/`,
      {
        credentials: 'include',
      }
    );

  if (!response.ok) {
    throw new Error(
      'Не вдалося завантажити послуги.'
    );
  }

  const data =
    await response.json();

    services = new Map(
        data.map(
            (service) => [
                Number(service.id),
                service,
            ]
        )
    );
}


async function loadBookings() {
  const response =
    await apiFetch(
      '/bookings/'
    );

  if (!response.ok) {
    throw new Error(
      'Не вдалося завантажити бронювання.'
    );
  }

  bookings =
    await response.json();
}


async function loadAdminData() {
  showAdminMessage(
    'Завантажуємо бронювання...'
  );

  refreshButton.disabled =
    true;

  try {
    await Promise.all([
      loadServices(),
      loadBookings(),
    ]);

    updateStats();

    renderBookings();

    showAdminMessage('');

  } catch (error) {
    showAdminMessage(
      error.message ||
      'Не вдалося завантажити дані.',
      true
    );

  } finally {
    refreshButton.disabled =
      false;
  }
}


async function updateBookingStatus(
  bookingId,
  newStatus,
  button
) {
  const statusName =
    STATUS_LABELS[newStatus] ||
    newStatus;

  const confirmed =
    window.confirm(
      `Змінити статус бронювання ` +
      `#${bookingId} на ` +
      `"${statusName}"?`
    );

  if (!confirmed) {
    return;
  }

  button.disabled = true;

  showAdminMessage(
    'Оновлюємо бронювання...'
  );

  try {
    const response =
      await apiFetch(
        `/bookings/${bookingId}/status`,
        {
          method: 'PATCH',

          headers: {
            'Content-Type':
              'application/json',
          },

          body: JSON.stringify({
            status: newStatus,
          }),
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
        data.detail ||
        'Не вдалося змінити статус.';

      if (
        response.status === 409
      ) {
        message =
          'Цей час уже зайнятий іншим підтвердженим бронюванням.';
      }

      if (
        response.status === 429
      ) {
        message =
          'Забагато запитів. Спробуйте трохи пізніше.';
      }

      throw new Error(message);
    }


    showAdminMessage(
      `Статус бронювання ` +
      `#${bookingId} оновлено.`
    );


    await loadBookings();

    updateStats();

    renderBookings();

  } catch (error) {
    showAdminMessage(
      error.message ||
      'Не вдалося оновити бронювання.',
      true
    );

  } finally {
    button.disabled = false;
  }
}


refreshButton.addEventListener(
  'click',
  loadAdminData
);


statusFilter.addEventListener(
  'change',
  renderBookings
);


dateFilter.addEventListener(
  'change',
  renderBookings
);


bookingSearch.addEventListener(
  'input',
  renderBookings
);


checkAdminSession();