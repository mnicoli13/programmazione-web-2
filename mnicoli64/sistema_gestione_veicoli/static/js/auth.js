// Document ready function for authentication
$(document).ready(function () {
  initAuthState();
  // Toggle password visibility
  $(".toggle-password").on("click", function () {
    const passwordInput = $(this).siblings("input");
    const icon = $(this).find("i");

    if (passwordInput.attr("type") === "password") {
      passwordInput.attr("type", "text");
      icon.removeClass("bi-eye").addClass("bi-eye-slash");
    } else {
      passwordInput.attr("type", "password");
      icon.removeClass("bi-eye-slash").addClass("bi-eye");
    }
  });

  // Username validation
  $("#register-username").on("input", function () {
    const username = $(this).val().trim();

    $(this).addClass("is-valid").removeClass("is-invalid");
    $("#username-feedback").html("").removeClass("text-danger");

    if (username.length < 4) {
      $("#username-feedback")
        .html("Il nome utente deve contenere almeno 4 caratteri")
        .addClass("text-danger")
        .removeClass("text-success");
      $(this).addClass("is-invalid").removeClass("is-valid");
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      $("#username-feedback")
        .html("Il nome utente può contenere solo lettere, numeri e underscore")
        .addClass("text-danger")
        .removeClass("text-success");
      $(this).addClass("is-invalid").removeClass("is-valid");
    }

    checkFormValidity();
  });

  // Email validation
  $("#register-email").on("input", function () {
    $(this).addClass("is-valid").removeClass("is-invalid");
    $("#email-feedback").html("").removeClass("text-danger");
    const email = $(this).val().trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
      $("#email-feedback")
        .html("Inserisci un indirizzo email valido")
        .addClass("text-danger")
        .removeClass("text-success");
      $(this).addClass("is-invalid").removeClass("is-valid");
    }

    checkFormValidity();
  });

  // Password strength check
  $("#register-password").on("input", function () {
    const password = $(this).val();
    const strengthInfo = checkPasswordStrength(password);

    // Update strength meter
    $("#password-strength-bar").css({
      width: strengthInfo.percentage + "%",
      "background-color": strengthInfo.color,
    });

    // Update feedback
    $("#password-feedback").html(strengthInfo.message);

    if (strengthInfo.score < 2) {
      $(this).addClass("is-invalid").removeClass("is-valid");
      $("#password-feedback")
        .addClass("text-danger")
        .removeClass("text-success text-warning");
    } else if (strengthInfo.score < 4) {
      $(this).addClass("is-valid").removeClass("is-invalid");
      $("#password-feedback")
        .addClass("text-warning")
        .removeClass("text-danger text-success");
    } else {
      $(this).addClass("is-valid").removeClass("is-invalid");
      $("#password-feedback")
        .addClass("text-success")
        .removeClass("text-danger text-warning");
    }

    // Also check the password confirmation
    checkPasswordMatch();
    checkFormValidity();
  });

  // Password confirmation check
  $("#register-confirm-password").on("input", function () {
    checkPasswordMatch();
    checkFormValidity();
  });

  // Terms checkbox
  $("#terms").on("change", function () {
    checkFormValidity();
  });

  // Login form submission
  $("#login-form").on("submit", function (e) {
    e.preventDefault();

    const formData = $(this).serialize();
    const loginButton = $(this).find('button[type="submit"]');
    const originalButtonText = loginButton.html();

    // Add loading state
    loginButton
      .html(
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Accesso in corso...'
      )
      .prop("disabled", true);

    $.ajax({
      url: URL_API_LOGIN,
      type: "POST",
      data: formData,
      dataType: "json",
      success: function (response) {
        if (response.success) {
          // Save user data to localStorage if "remember me" is checked
          if ($("#remember-me").is(":checked")) {
            localStorage.setItem(
              "user",
              JSON.stringify({
                id: response.user.id,
                username: response.user.username,
                email: response.user.email,
              })
            );
          }

          // Show success message and redirect
          showLoginNotification(
            "Accesso effettuato con successo! Reindirizzamento...",
            "success"
          );

          setTimeout(function () {
            window.location.href = "dashboard";
          }, 1500);
        } else {
          loginButton.html(originalButtonText).prop("disabled", false);
          showLoginNotification(response.message, "danger");
        }
      },
      error: function () {
        loginButton.html(originalButtonText).prop("disabled", false);
        showLoginNotification(
          "Errore di comunicazione con il server",
          "danger"
        );
      },
    });
  });

  // Register form submission
  $("#register-form").on("submit", async function (e) {
    e.preventDefault();

    // Validate format first
    if (!checkFormValidity(false)) {
      return;
    }

    const formData = $(this).serialize();
    const registerButton = $(this).find('button[type="submit"]');
    const originalButtonText = registerButton.html();

    // Add loading state
    registerButton
      .html(
        '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifica dati...'
      )
      .prop("disabled", true);

    // Check username and email availability
    const username = $("#register-username").val().trim();
    const email = $("#register-email").val().trim();
    // Submit registration
    ajaxRegister(username, email, formData, registerButton, originalButtonText);
  });

  // Handle logout
  $("#logout-button").on("click", function (e) {
    e.preventDefault();

    $.ajax({
      url: "../api/auth/logout.php",
      type: "POST",
      dataType: "json",
      success: function (response) {
        if (response.success) {
          // Clear localStorage
          localStorage.removeItem("user");

          // Redirect to login page
          window.location.href = "login.php";
        }
      },
    });
  });
});

// Function to show notification in the login/register form
function showLoginNotification(message, type) {
  $("#login-notification")
    .html(
      `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `
    )
    .show();
}

// Set user menu state based on authentication
function setUserMenuState(user) {
  // Update user menu with user info
  if ($("#user-menu").length) {
    $("#user-menu-username").text(user.username);
    $("#user-menu-dropdown").show();
    $("#login-button").hide();
  }
}

// Function to check overall form validity
function checkFormValidity(skipExistence = true) {
  const usernameValid = $("#register-username").hasClass("is-valid");
  const emailValid = $("#register-email").hasClass("is-valid");
  const passwordValid = $("#register-password").hasClass("is-valid");
  const passwordsMatch = checkPasswordMatch();
  const termsAccepted = $("#terms").is(":checked");

  if (
    usernameValid &&
    emailValid &&
    passwordValid &&
    passwordsMatch &&
    termsAccepted
  ) {
    $("#register-button").prop("disabled", false);
    return true;
  } else {
    $("#register-button").prop("disabled", true);
    return false;
  }
}

// Function to check password strength
function checkPasswordStrength(password) {
  // Default values
  let score = 0;
  let message = "Inserisci una password";
  let color = "#dc3545"; // Bootstrap danger

  if (password.length === 0) {
    return { score, message, color, percentage: 0 };
  }

  // Length check
  if (password.length < 8) {
    message = "La password è troppo corta (minimo 8 caratteri)";
    score = 1;
  } else {
    score++;

    // Check for lowercase letters
    if (/[a-z]/.test(password)) score++;

    // Check for uppercase letters
    if (/[A-Z]/.test(password)) score++;

    // Check for numbers
    if (/[0-9]/.test(password)) score++;

    // Check for special characters
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    // Set message based on score
    switch (score) {
      case 2:
        message = "Password debole";
        color = "#dc3545"; // Bootstrap danger
        break;
      case 3:
        message = "Password moderata";
        color = "#ffc107"; // Bootstrap warning
        break;
      case 4:
        message = "Password buona";
        color = "#28a745"; // Bootstrap success
        break;
      case 5:
        message = "Password eccellente";
        color = "#28a745"; // Bootstrap success
        break;
    }
  }

  // Calculate percentage for the strength meter
  const percentage = (score / 5) * 100;

  return { score, message, color, percentage };
}

// Function to check password match
function checkPasswordMatch() {
  const password = $("#register-password").val();
  const confirmPassword = $("#register-confirm-password").val();

  if (confirmPassword.length === 0) {
    $("#confirm-password-feedback").html("");
    $("#register-confirm-password").removeClass("is-valid is-invalid");
    return false;
  }

  if (password === confirmPassword) {
    $("#confirm-password-feedback")
      .html("")
      .addClass("text-success")
      .removeClass("text-danger");
    $("#register-confirm-password")
      .addClass("is-valid")
      .removeClass("is-invalid");
    return true;
  } else {
    $("#confirm-password-feedback")
      .html("Le password non corrispondono")
      .addClass("text-danger")
      .removeClass("text-success");
    $("#register-confirm-password")
      .addClass("is-invalid")
      .removeClass("is-valid");
    return false;
  }
}

async function ajaxRegister(
  username,
  email,
  formData,
  registerButton,
  originalButtonText
) {
  $.ajax({
    url: URL_API_CHECK_USERNAME,
    type: "POST",
    data: { username: username },
    dataType: "json",
    success: function (usernameResponse) {
      if (!usernameResponse.available) {
        $("#username-feedback")
          .html("Nome utente già in uso")
          .addClass("text-danger")
          .removeClass("text-success");
        $("#register-username").addClass("is-invalid").removeClass("is-valid");

        registerButton.html(originalButtonText).prop("disabled", false);
        return false;
      }

      $.ajax({
        url: URL_API_CHECK_EMAIL,
        type: "POST",
        data: { email: email },
        dataType: "json",
        success: function (emailResponse) {
          if (!emailResponse.available) {
            $("#email-feedback")
              .html("Email già registrata")
              .addClass("text-danger")
              .removeClass("text-success");
            $("#register-email").addClass("is-invalid").removeClass("is-valid");

            registerButton.html(originalButtonText).prop("disabled", false);
            return false;
          }

          $.ajax({
            url: URL_API_REGISTER,
            type: "POST",
            data: formData,
            dataType: "json",
            success: function (response) {
              if (response.success) {
                // Show success message
                showLoginNotification(
                  "Registrazione completata con successo! Ora puoi accedere con le tue credenziali.",
                  "success"
                );

                // Switch to login tab
                $("#login-tab").tab("show");

                // Pre-fill the login form with the username
                $("#login-username").val($("#register-username").val());

                // Reset the register form
                $("#register-form")[0].reset();
                $("#register-button").prop("disabled", true);
                $("#password-strength-bar").css("width", "0%");
              } else {
                registerButton.html(originalButtonText).prop("disabled", false);
                showLoginNotification(response.message, "danger");
              }
            },
            error: function () {
              registerButton.html(originalButtonText).prop("disabled", false);
              showLoginNotification(
                "Errore di comunicazione con il server",
                "danger"
              );
            },
          });
        },
        error: function () {
          registerButton.html(originalButtonText).prop("disabled", false);
          showLoginNotification("Errore nella verifica dell'email", "danger");
          return false;
        },
      });
    },
    error: function () {
      registerButton.html(originalButtonText).prop("disabled", false);
      showLoginNotification("Errore nella verifica del nome utente", "danger");
      return false;
    },
  });
}
