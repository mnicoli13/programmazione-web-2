// Document ready function for CRUD operations
$(document).ready(function () {
  // Add Vehicle from empty state
  $("#add-veicolo-empty-btn").on("click", function () {
    $("#addVeicoloModal").modal("show");
  });

  // Save new vehicle
  $("#save-add-veicolo").on("click", function () {
    $(this).prop("disabled", true);
    const form = $("#add-veicolo-form");

    // Form validation
    if (!form[0].checkValidity()) {
      form[0].reportValidity();
      $(this).prop("disabled", false);
      return;
    }

    // Collect form data
    const formData = new FormData(form[0]);

    // Send data
    $.ajax({
      url: URL_API_ADD_VEICOLO,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        if (response.status === "success") {
          // Close modal
          $("#addVeicoloModal").modal("hide");

          // Reset form
          form[0].reset();

          // Show notification
          showNotification(
            '<i class="bi bi-check-circle"></i> ' + response.message,
            "success"
          );

          // Reload data
          loadTableData("");
        } else {
          showNotification(
            '<i class="bi bi-exclamation-triangle"></i> ' + response.message,
            "danger"
          );
        }
      },
      error: function () {
        showNotification(
          '<i class="bi bi-exclamation-triangle"></i> Errore durante la comunicazione con il server',
          "danger"
        );
      },
      complete: function () {
        $("#save-add-veicolo").prop("disabled", false);
      },
    });
  });

  // Handler per il pulsante modifica nella tabella
  $(document).on("click", ".edit-btn", function () {
    $(this).prop("disabled", true);
    const id = $(this).data("id");

    // Carica i dati del veicolo
    $.ajax({
      url: URL_API_VEICOLI,
      type: "GET",
      data: { telaio: id },
      dataType: "json",
      success: function (response) {
        if (response.status === "success") {
          // Popolamento form
          $("#edit-original-telaio").val(response.data[0].telaio);
          $("#edit-telaio").val(response.data[0].telaio);
          $("#edit-marca").val(response.data[0].marca);
          $("#edit-modello").val(response.data[0].modello);
          $("#edit-dataProd").val(response.data[0].dataProd);

          // Mostra modale
          $("#editVeicoloModal").modal("show");
        } else {
          showNotification(
            '<i class="bi bi-exclamation-triangle"></i> ' + response.message,
            "danger"
          );
        }
      },
      error: function () {
        showNotification(
          '<i class="bi bi-exclamation-triangle"></i> Errore durante il caricamento dei dati del veicolo',
          "danger"
        );
      },
      complete: function () {
        $(".edit-btn").prop("disabled", false);
      },
    });
  });

  // Edit vehicle handler
  $("#save-edit-veicolo").on("click", function () {
    $(this).prop("disabled", true);
    const form = $("#edit-veicolo-form");
    const telaio = $("#edit-telaio").val();

    // Get the URL using the function
    const updateUrl = URL_API_UPDATE_VEICOLO(telaio);

    // Form validation
    if (!form[0].checkValidity()) {
      form[0].reportValidity();
      $(this).prop("disabled", false);
      return;
    }

    // Collect form data
    const formData = new FormData(form[0]);

    // Send data
    $.ajax({
      url: updateUrl,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        if (response.status === "success") {
          // Close modal
          $("#editVeicoloModal").modal("hide");

          // Show notification
          showNotification(
            '<i class="bi bi-check-circle"></i> ' + response.message,
            "success"
          );

          // Reload data
          loadTableData("");
        } else {
          showNotification(
            '<i class="bi bi-exclamation-triangle"></i> ' + response.message,
            "danger"
          );
        }
      },
      error: function () {
        showNotification(
          '<i class="bi bi-exclamation-triangle"></i> Errore durante la comunicazione con il server',
          "danger"
        );
      },
      complete: function () {
        $("#save-edit-veicolo").prop("disabled", false);
      },
    });
  });

  // Handler per il pulsante elimina nella tabella
  $(document).on("click", ".delete-btn", function () {
    $(this).prop("disabled", true);
    const id = $(this).data("id");
    $("#delete-telaio").val(id);
    $("#delete-telaio-display").text(id);
    $("#deleteVeicoloModal").modal("show");
    $(this).prop("disabled", false);
  });

  // Delete vehicle handler
  $("#confirm-delete-veicolo").on("click", function () {
    $(this).prop("disabled", true);
    const form = $("#delete-veicolo-form");
    const formData = new FormData(form[0]);
    const telaio = $("#delete-telaio").val();

    // Get the URL using the function
    const deleteUrl = URL_API_DELETE_VEICOLO(telaio);

    $.ajax({
      url: deleteUrl,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        if (response.status === "success") {
          // Close modal
          $("#deleteVeicoloModal").modal("hide");

          // Show notification
          showNotification(
            '<i class="bi bi-check-circle"></i> ' + response.message,
            "success"
          );

          // Reload data
          loadTableData("");
        } else {
          showNotification(
            '<i class="bi bi-exclamation-triangle"></i> ' + response.message,
            "danger"
          );
        }
      },
      error: function () {
        showNotification(
          '<i class="bi bi-exclamation-triangle"></i> Errore durante la comunicazione con il server',
          "danger"
        );
      },
      complete: function () {
        $("#confirm-delete-veicolo").prop("disabled", false);
      },
    });
  });
});
