function createNotification(id, title, application, text, status) {
    let toastId = 'notification' + id;

    let status_map = ['success', 'info', 'warning', 'danger'];
    status = status_map[status];

    let application_map = ['API', 'Trésorerie', 'Gestionnaire', 'Magellans', 'Membres', 'Vitrine', 'Magasin'];
    application = application_map[application];

    // Construct the toast HTML
    let toastHTML = '<div id="' + toastId + '" class="toast bg-dark text-white" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000">' +
                    '  <div class="toast-header bg-dark">' +
                    '    <strong class="me-auto">' + title + '</strong>' +
                    '    <small> ' + application + '</small>' +
                    '    <button type="button" class="btn-close" onclick="closeNotification(\'#'+ toastId +'\')">' +
                    '    </button>' +
                    '  </div>' +
                    '  <div class="toast-body bg-' + status + '">' +
                         text +
                    '  </div>' +
                    '</div>';

    // Append the toast to the body
    $('#notificationContainer').append(toastHTML);

    // Show the toast
    let toast = $('#' + toastId) ;
    toast.toast('show');

    return toast
}

function closeNotification(id) {
    $(id).toast('hide');
}

const notificationSocket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");

notificationSocket.onopen = () => {
    console.log("Notification socket connected")
}

notificationSocket.onmessage = (event) => {
    let json_data = JSON.parse(event.data).notification;
    let notification = createNotification(json_data.id, json_data.title, json_data.application, json_data.message, json_data.status);
}

notificationSocket.onclose = () => {
    console.log("Notification socket closed.");
}