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