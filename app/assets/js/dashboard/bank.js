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

async function addOperation(callback = function(){}) {
    let action = "add-operation";
    let params = {
        token: api_token,
        action: action,
        desc: document.querySelector("#id_desc").value,
        type: document.querySelector("#id_type").value,
        third_party: document.querySelector("#id_third_party").value,
        amount: document.querySelector("#id_amount").value,
        date: document.querySelector("#id_date").value
    }

    let response = await sendApiRequest(params, "bank");

    if(response.status == "success") {
        callback(response);
    }
}