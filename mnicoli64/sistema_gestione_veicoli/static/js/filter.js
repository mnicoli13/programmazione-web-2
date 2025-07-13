// Document ready function for filter functionality
$(document).ready(function () {
  // Submit filter form
  $("#filter-form").on("submit", function (e) {
    e.preventDefault();
    const filterData = $(this).serialize();

    // Show loading state
    console.log("table loader show: ", $(".table-loader"));
    $(".table-loader").show();

    loadTableData(filterData);

    console.log("table loader hide: ", $(".table-loader"));
    $(".table-loader").hide();

    // Aggiorna status filtri
    updateFilterStatus();

    // Show feedback that filters are applied
    showNotification(
      '<i class="bi bi-funnel"></i> Filtri applicati con successo',
      "info"
    );
  });

  // Reset filter form
  $("#reset-filter").on("click", function () {
    $("#filter-form")[0].reset();
    loadTableData("");

    // Nascondi status filtri
    $("#filter-status").addClass("d-none");

    // Show feedback that filters are reset
    showNotification(
      '<i class="bi bi-arrow-counterclockwise"></i> Filtri reimpostati',
      "info"
    );
  });

  // Clear filters
  $("#filter-clear-btn").on("click", function () {
    $("#reset-filter").click();
  });

  // Toggle filter collapse - aggiorna icona
  $('[data-bs-toggle="collapse"]').on("click", function () {
    const icon = $(this).find("i");
    icon.toggleClass("bi-chevron-up bi-chevron-down");
  });

  // Gestione URL parametri per filtri con deep linking
  const urlParams = new URLSearchParams(window.location.search);
  let hasFilters = false;

  // Se ci sono parametri di filtro, li applichiamo
  $("#filter-form")
    .find("input, select")
    .each(function () {
      const fieldName = $(this).attr("name");
      if (urlParams.has(fieldName)) {
        const fieldValue = urlParams.get(fieldName);
        $(this).val(fieldValue);
        hasFilters = true;
      }
    });

  if (hasFilters) {
    // Submit form se abbiamo trovato parametri
    $("#filter-form").trigger("submit");
  } else {
    // Carica dati senza filtri
    loadTableData("");
  }
});

// Function to update filter status indicators
function updateFilterStatus() {
  const activeFilters = [];

  $("#filter-form")
    .find("input, select")
    .each(function () {
      const fieldValue = $(this).val();
      if (fieldValue) {
        const fieldName = $(this).attr("name");
        const fieldLabel = $("label[for='filter-" + fieldName + "']").text();
        activeFilters.push(fieldLabel + ": " + fieldValue);
      }
    });

  if (activeFilters.length > 0) {
    $("#filter-status-text").html(
      '<i class="bi bi-funnel-fill me-1"></i> Filtri attivi: ' +
      activeFilters.join(", ")
    );
    $("#filter-status").removeClass("d-none");
  } else {
    $("#filter-status").addClass("d-none");
  }
}

// Function to show notifications
function showNotification(message, type = "info") {
  let notificationHtml =
    '<div class="alert alert-' +
    type +
    ' alert-dismissible fade show" role="alert">';
  notificationHtml += message;
  notificationHtml +=
    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
  notificationHtml += "</div>";

  $("#notification-area").html(notificationHtml);

  // Auto-hide after 5 seconds
  setTimeout(function () {
    $(".alert").alert("close");
  }, 5000);
}

// Function to load table data with filters
function loadTableData(filterData) {
  console.log("loadTableData");

  const tableName = $("#table-container").data("table-name");

  console.log(filterData + "&table=" + tableName);

  // Show loading state
  $(".table-loader").show();

  // Hide empty state if visible
  $("#empty-state").hide();

  $.ajax({
    url: URL_API_TABLE,
    type: "GET",
    data: filterData + "&table=" + tableName,
    dataType: "json",
    success: function (response) {
      if (response.status === "success") {
        if (response.data.length === 0) {
          // Show empty state
          $("#empty-state").show();
          $("#table-container").hide();
        } else {
          $("#empty-state").hide();
          $("#table-container").show();

          // ─── ESTRAGGO sort e order da filterData ─────────────────────────────
          const params = new URLSearchParams(filterData);
          const sortField = params.get("sort") || null;
          const sortOrder = params.get("order") || null;
          // ──────────────────────────────────────────────────────────────────────

          renderTable(
            response.data,
            response.columns,
            tableName,
            sortField,
            sortOrder
          );
        }
      } else {
        $("#table-container").html(
          '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle"></i> Errore nel caricamento dei dati: ' +
          response.message +
          "</div>"
        );
      }
    },
    error: function (xhr, status, error) {
      $("#table-container").html(
        '<div class="alert alert-danger"><i class="bi bi-wifi-off"></i> Errore di comunicazione con il server: ' +
        error +
        "</div>"
      );
    },
  });

  $(".table-loader").hide();
}

function renderTable(
  data,
  columns,
  tableName,
  sortField = null,
  sortOrder = "asc"
) {
  const $table = $("#myTable");
  const $thead = $table.find("thead");
  const $tbody = $table.find("tbody");

  console.log("renderTable");

  // 1) Aggiorna i data-order e le icone sugli <th>
  $thead.find("th.sortable").each(function () {
    const $th = $(this);
    const col = $th.data("column");
    const isSorted = col === sortField;
    const order = isSorted ? sortOrder : "asc";
    const icon = isSorted
      ? `bi-arrow-${sortOrder === "asc" ? "up" : "down"}`
      : "bi-arrow-down-up text-muted small";

    $th
      .data("order", order)
      .find("i")
      .attr("class", "bi " + icon);
  });

  // 2) Popola il <tbody>
  $tbody.empty();
  data.forEach((row) => {
    let $tr = $("<tr>");
    columns.forEach((col) => {
      let cell = row[col.name] || "";

      if (col.type === "date") {
        cell = cell ? formatDate(cell) : "";
      } else if (col.type === "status") {
        let badgeClass = "",
          icon = "";
        switch (cell) {
          case "Attiva":
            badgeClass = "bg-success";
            icon = "bi-check-circle-fill";
            break;
          case "Restituita":
            badgeClass = "bg-warning text-dark";
            icon = "bi-arrow-return-left";
            break;
          default:
            badgeClass = "bg-secondary";
            icon = "bi-dash-circle";
        }
        cell = `<span class="badge ${badgeClass}"><i class="bi ${icon} me-1"></i>${cell}</span>`;
      } else if (col.isLink) {
        // cell = `<a href="./${col.linkTarget}.php?${col.name
        //   }=${cell}" class="table-link" data-target="${col.linkTarget
        //   }" data-value="${row[col.name]}">${cell}</a>`;

        cell = `<a href="../${col.linkTarget}" class="table-link" data-target="${col.linkTarget}" data-value="${row[col.name]}">${cell}</a>`;

      }
      $tr.append($("<td>").html(cell));
    });

    console.log("tableName: ", tableName);

    // azioni su Veicolo
    if (tableName === "veicolo") {
      const editBtn = `<button class="btn btn-sm btn-primary edit-btn" data-id="${row.telaio}"><i class="bi bi-pencil"></i></button>`;
      const deleteBtn = `<button class="btn btn-sm btn-danger delete-btn" data-id="${row.telaio}"><i class="bi bi-trash"></i></button>`;
      $tr.append(
        $("<td class='text-center d-flex gap-3 justify-content-end'>").html(
          editBtn + deleteBtn
        )
      );
    }

    $tbody.append($tr);
  });

  // 3) Ricollega i listener

  // Sorting
  $thead
    .find("th.sortable")
    .off("click")
    .on("click", function (e) {
      e.preventDefault();
      const $th = $(this);
      const column = $th.data("column");
      const current = $th.data("order");
      const next = current === "asc" ? "desc" : "asc";
      const params =
        $("#filter-form").serialize() + "&sort=" + column + "&order=" + next;
      loadTableData(params);
    });
}

// Function to format date for display
function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("it-IT");
}
