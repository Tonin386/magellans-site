async function editOrderStatus(pk, value, callback = function(){}) {
    let action = "edit-order_status";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
        value: value
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}

async function sendOrderStatusEmail(pk, callback = function(){}) {
    let action = "email-order_status";
    let message = document.querySelector("#custom_message");

    let params = {
        token: api_token,
        action: action,
        message: message.value,
        pk: pk,
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}