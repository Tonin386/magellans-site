async function addResource(callback = function(){}) {
    let action = "add-resource";
    let params = {
        token: api_token,
        action: action,
        name: document.querySelector("#resource_name").value.trim(),
        file: document.querySelector("#resource_file").files[0],
        desc: document.querySelector("#resource_desc").value.trim(),
        category: document.querySelector("#resource_category").value.trim(),
    };

    if(params["file"]) {
        const fileName = params.file.name;
        const base64file = await toBase64(params['file']);
        params['file'] = base64file;
        params['fileName'] = fileName;
    }

    let response = await sendApiRequest(params, "members");

    console.log(params);

    if(response.status == "success") {
        callback(response);
    }
}