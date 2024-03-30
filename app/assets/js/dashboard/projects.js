async function addProject(callback = function(){}) {
    let action = "add-project";
    let params = {
        token: api_token,
        action: action,
        name: document.querySelector("#project_name").value,
        director: document.querySelector("#select_director").value,
        money_handler: document.querySelector("#select_money_handler").value,
        genre: document.querySelector("#project_genre").value,
        short_desc: document.querySelector("#project_short_desc").value,
        desc: document.querySelector("#project_desc").value,
        shoot_date: document.querySelector("#project_shoot_date").value,
        release_date: document.querySelector("#project_release_date").value,
        poster: document.querySelector("#project_poster").files[0],
        public: document.querySelector("#project_public").checked
    };

    if(params["poster"]) {
        const base64Image = await toBase64(params['poster']);
        params['poster'] = base64Image;
    }
    
    let response = await sendApiRequest(params, "dashboard");

    if(response.status == "success") {
        callback(response);
    }
}

async function editProject(slug, callback = function(){}) {
    let action = "edit-project";
    let params = {
        token: api_token,
        action: action,
        slug: slug,
        name: document.querySelector("#project_name").value,
        director: document.querySelector("#select_director").value,
        money_handler: document.querySelector("#select_money_handler").value,
        genre: document.querySelector("#project_genre").value,
        short_desc: document.querySelector("#project_short_desc").value,
        desc: document.querySelector("#project_desc").value,
        shoot_date: document.querySelector("#project_shoot_date").value,
        release_date: document.querySelector("#project_release_date").value,
        poster: document.querySelector("#project_poster").files[0],
        public: document.querySelector("#project_public").checked
    };

    if(params["poster"]) {
        const base64Image = await toBase64(params['poster']);
        params['poster'] = base64Image;
    }
    
    let response = await sendApiRequest(params, "dashboard");
    
    if(response.status == "success") {
        callback(response);
    }
}