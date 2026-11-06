// Confirmação antes de enviar formulários marcados com data-confirm
// (arquivo externo porque a CSP não permite scripts inline).
document.addEventListener("submit", function (event) {
  var message = event.target.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});
