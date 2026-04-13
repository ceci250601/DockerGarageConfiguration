// =============================================================================
// script.js - Gestione interfaccia Calendario (frontend)
// Coerenza con API Flask definite in app.py
// -----------------------------------------------------------------------------
// API rilevanti in app.py:
//   - GET  /calendar        → mostra pagina calendario con auto abilitate
//   - POST /calendar/save   → salva configurazione ricevuta in formato JSON
//
// Questo script:
//   - gestisce i checkbox "Partenza" e "Resta ferma" per ogni auto
//   - costruisce un array JSON con le scelte fatte
//   - invia i dati a /calendar/save tramite fetch POST
// =============================================================================


// ==============================
//  Utility functions
// ==============================
function qs(root, sel)    { return root.querySelector(sel); }
function qsa(root, sel)   { return root.querySelectorAll(sel); }
function on(el, ev, cb)   { el && el.addEventListener(ev, cb, { passive: false }); }

// DOM ready helper
function ready(cb) {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', cb);
  } else {
    cb();
  }
}


// ==============================
//  CALENDARIO: gestione checkbox + invio a /calendar/save
// ==============================
function initCalendarForms() {
  const forms = qsa(document, ".calendar-form");
  if (!forms.length) return;

  // Configura i checkbox per ogni auto
  forms.forEach(card => {
    const depart = qs(card, ".mode.depart");
    const idle = qs(card, ".mode.idle");
    const timeInput = qs(card, ".time-input");
    const timeRow = qs(card, ".time-row");

    function updateState() {
      if (depart.checked) {
        idle.checked = false;
        timeInput.disabled = false;
        timeRow.classList.remove("is-disabled");
      } else if (idle.checked) {
        depart.checked = false;
        timeInput.value = "";
        timeInput.disabled = true;
        timeRow.classList.add("is-disabled");
      } else {
        timeInput.disabled = true;
        timeInput.value = "";
        timeRow.classList.add("is-disabled");
      }
    }

    on(depart, "change", updateState);
    on(idle, "change", updateState);
    updateState(); // stato iniziale
  });

  // Bottone "Salva configurazione"
  const saveBtn = qs(document, "#saveCalendarBtn");
  if (saveBtn) {
    on(saveBtn, "click", () => {
      const carsData = [];
      let valid = true;
      let errorMsg = "";

      forms.forEach(card => {
        const carName = card.dataset.car;
        const depart = qs(card, ".mode.depart").checked;
        const idle = qs(card, ".mode.idle").checked;
        const time = qs(card, ".time-input").value;

        let mode;

        if (depart && time) {
          mode = "depart";
        } else if (idle) {
          mode = "idle";
        } else {
          valid = false;
          errorMsg += `⚠️ Completa la configurazione per: ${carName}\n`;
          card.style.border = "2px solid red";
          return;
        }

        // Se valido, rimuovi evidenziazione errore
        card.style.border = "";

        carsData.push({ car: carName, mode, time });
      });

      if (!valid) {
        alert("Errore:\n" + errorMsg);
        return;
      }

      // Invio POST a /calendar/save
      fetch("/calendar/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(carsData)
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert("Errore: " + data.error);
        } else {
          alert("Configurazione salvata!");
          console.log("Risposta server:", data);
        }
      })
      .catch(err => {
        console.error("Errore:", err);
        alert("Errore nel salvataggio.");
      });
    });
  }
}


// ==============================
//  Init
// ==============================
ready(() => {
  initCalendarForms();
});
