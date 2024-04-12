async function editInvoiceStatus(pk, value, callback = function() {}) { 
    let action = "edit-invoice_status";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
        value: value
    };
    
    let response = await sendApiRequest(params, "bank");
    
    if(response.status == "success") {
        callback(response);
    }
}

async function sendInvoiceStatusEmail(pk, callback = function(){}) {
    let action = "email-invoice_status";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
    };
    
    let response = await sendApiRequest(params, "bank");
    
    if(response.status == "success") {
        callback(response);
    }
}