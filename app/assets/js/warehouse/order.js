(function () {
    'use strict';

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('.needs-validation');

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity() || !checkDateOrder()) {
                    event.preventDefault();
                    event.stopPropagation();
                }

                form.classList.add('was-validated');
            }, false);
        });

    function checkDateOrder() {
        var startDateField = document.getElementById('id_start_date');
        var endDateField = document.getElementById('id_end_date');
        var form = document.querySelector(".needs-validation");

        var startDate = startDateField.value;
        var endDate = endDateField.value;

        if (startDate && endDate) {
            if (startDate > endDate) {
                document.getElementById('dateError').style.display = 'block';
                startDateField.classList.remove("is-valid");
                startDateField.classList.add("is-invalid");
                endDateField.classList.remove("is-valid");
                endDateField.classList.add("is-invalid");
                form.classList.remove("was-validated");
                return false;
            } else {
                document.getElementById('dateError').style.display = 'none';
                startDateField.classList.add("is-valid");
                startDateField.classList.remove("is-invalid");
                endDateField.classList.add("is-valid");
                endDateField.classList.remove("is-invalid");
                form.classList.add("was-validated");
                return true;
            }
        }

        return true;
    }

    // Validate date on change
    document.getElementById('id_start_date').addEventListener('change', function() {
        checkDateOrder();
    });

    document.getElementById('id_end_date').addEventListener('change', function() {
        checkDateOrder();
    });
})();