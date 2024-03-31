async function sendApiRequest(params, app) {
    for(key in params) {
        if(params[key] == null || params[key].length == 0) {
            delete params[key];
        }
    }

    const url = window.location.origin + "/api/" + app;
    let request = {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            'X-Requested-With': 'XMLHttpRequest',
        }
    }
    
    try {
        let response = await fetch(url, request);
        if(!response.ok) {
            throw new Error('Failed to fetch api response');
        }
        
        const data = await response.json();
        return data;
    }
    catch (error){
        console.log(error);
    }
} 

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function printApiToken() {
    console.log(api_token);
}

const toBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
});
