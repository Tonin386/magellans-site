function createNotification(id, title, application, text, status) {
    let toastId = 'notification' + id;

    let status_map = ['success', 'info', 'warning', 'danger'];
    status = status_map[status];

    let application_map = ['API', 'Trésorerie', 'Gestionnaire', 'Magellans', 'Membres', 'Vitrine', 'Magasin'];
    application = application_map[application];

    // Construct the toast HTML
    let toastHTML = '<div id="' + toastId + '" class="toast bg-dark text-white" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000">' +
                    '  <div class="toast-header bg-dark">' +
                    '    <span class="me-auto text-light">' + title + '</span>' +
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

    return toast;
}

function closeNotification(id) {
    $(id).toast('hide');
}


try {
    var unsecureNotificationSocket = new WebSocket("ws://" + window.location.host + "/ws/notifications/");

    unsecureNotificationSocket.onerror = () => {
        console.log("Failed to use unsecure protocol.");
        unsecureNotificationSocket.close();
    }
    unsecureNotificationSocket.onopen = () => {
        console.log("Unsecure notification socket connected")
    }
    unsecureNotificationSocket.onmessage = (event) => {
        let json_data = JSON.parse(event.data).notification;
        let notification = createNotification(json_data.id, json_data.title, json_data.application, json_data.message, json_data.status);
    }
    unsecureNotificationSocket.onclose = () => {
        console.log("Unsecure notification socket closed.");
    }
}
catch(error) {

    var secureNotificationSocket = new WebSocket("wss://" + window.location.host + "/ws/notifications/");

    secureNotificationSocket.onerror = () => {
        console.log("Failed to use secure protocol.");
        secureNotificationSocket.close();
    }
    secureNotificationSocket.onopen = () => {
        console.log("Secure notification socket connected")
    }
    secureNotificationSocket.onmessage = (event) => {
        let json_data = JSON.parse(event.data).notification;
        let notification = createNotification(json_data.id, json_data.title, json_data.application, json_data.message, json_data.status);
    }
    secureNotificationSocket.onclose = () => {
        console.log("Secure notification socket closed.");
    }
}


