function submitInvoice() {
    let form = document.querySelector("form.needs-validation");
    form.classList.add("was-validated");
    if(form.checkValidity()) {
        form.submit();
    }
}