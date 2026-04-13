GarageConfiguration - Software per la gestione del Garage

Nome progetto
------------
GarageConfiguration — Software per la gestione di un garage con interfaccia web
(sezioni garage, gestione auto, calendario partenze).

Descrizione
----------
Un'app leggera che:
- gestisce un elenco di auto (brand, model, color, disabled);
- permette di configurare il numero di sezioni del garage;
- consente impostare un calendario di partenze (o lasciare l'auto "idle");
- salva dati in file JSON / TXT su disco per semplicità (nessun DB esterno).

Il progetto include:
- app.py — server e rotte principali;
- garage_utils.py — classe Car e CarManager per persistenza su JSON;
- templates/ — pagine Jinja2 (index, calendar, select_cars, edit_car, edit_sections);
- static/ — css/style.css, js/script.js e risorse frontend;
- data files attesi: cars.json, appointments.json, garage_sections.txt.

Prerequisiti
-----------
- Python 3.10+ (o versione compatibile con typing usato nel codice)
- pip
- (opzionale) ambiente virtuale

Installazione locale
--------------------
1. Clona il repository:
   git clone <URL_DEL_REPO>
   cd GarageConfiguration

2. Crea e attiva un ambiente virtuale (opzionale ma consigliato):
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scriptsctivate      # Windows (PowerShell: .venv\Scripts\Activate.ps1)

3. Installa dipendenze:
   pip install Flask
   # se vuoi creare requirements:
   pip freeze > requirements.txt

Configurazione
-------------
Variabili d'ambiente utili:
- SECRET_KEY — chiave segreta Flask (default: "cambia_questa_chiave_super_segreta")
- DATA_DIR — directory dove vengono salvati i file (default: /app/data)

Esempio (Linux/macOS):
   export SECRET_KEY="una_chiave_lunga_e_segreta"
   export DATA_DIR="./data"

Struttura dati / file
---------------------
Il progetto usa i seguenti file nella directory DATA_DIR (creali se non esistono):

- cars.json — lista auto (array di oggetti)
  Esempio:
  [
    {"brand": "Fiat", "model": "500", "color": "#ff0000", "disabled": false},
    {"brand": "Toyota", "model": "Yaris", "color": "#00ff00", "disabled": true}
  ]

- appointments.json — lista appuntamenti/calendario (array)
  Ogni elemento:
  [
    {"car": "500", "mode": "depart", "time": "08:30"},
    {"car": "Yaris", "mode": "idle", "time": ""}
  ]

- garage_sections.txt — singolo valore intero che rappresenta il numero di sezioni
  Esempio: file contenente solo "6"

Note:
- CarManager legge/scrive il file passato in inizializzazione (default: selected_cars.json nel working dir, ma app.py passa CARS_JSON)
- Se i file non esistono, l'app è in grado di lavorare (vengono create liste vuote), ma è consigliabile inizializzarli per testare l'interfaccia.

Esecuzione
---------
Avvia l'app in modalità sviluppo:
   export FLASK_APP=app.py
   export FLASK_ENV=development     # opzionale: abilita debug
   python app.py
# oppure
   flask run --host=0.0.0.0 --port=8000

L'app sarà disponibile su http://0.0.0.0:8000 (o http://localhost:8000).

Rotte principali (API e pagine)
-------------------------------
- GET /             → Pagina principale con visualizzazione sezioni garage
- GET /calendar     → Pagina calendario (mostra auto abilitate)
- POST /calendar/save → Salva la configurazione del calendario
  - Body: JSON array, ogni elemento:
    {"car": "MODEL", "mode": "depart" | "idle", "time": "HH:MM"}
  - Risposte:
    - 200: {"status":"ok","saved": [... ]}
    - 400/500: {"error": "..."}
- GET, POST /select_cars → Gestione aggiunta auto (form)
- GET /select_cars/remove/<int:index> → Rimuove auto per indice
- GET, POST /select_cars/edit/<int:index> → Modifica singola auto
- GET, POST /edit_sections → Imposta numero di sezioni del garage
- GET /cars → Vista tabellare delle auto

Frontend
--------
- templates/*.html contengono le pagine Jinja2 (calendar.html, select_cars.html, edit_car.html, edit_sections.html, index.html)
- static/css/style.css → stili moderni e responsivi del progetto
- static/js/script.js → logica client-side per il calendario (costruzione JSON e POST a /calendar/save)

Logica colore
-------------
Il modulo contiene utilità per convertire colori hex/nome CSS in RGB e determinare se un colore è chiaro
(per applicare bordi o stili particolari alle auto).

Buone pratiche e note di sviluppo
--------------------------------
- Non inserire chiavi sensibili direttamente nel repo (usa variabili d'ambiente).
- Assicurati che la directory DATA_DIR sia scrivibile dal processo Flask.
- Per ambienti di produzione, disattiva debug ed usa un WSGI server (es. gunicorn) e un reverse proxy (es. nginx).
- Se più utenti modificano gli stessi file, considera il passaggio a un DB (SQLite/Postgres) per evitare race condition.

Test & debugging
----------------
- Verifica i permessi della cartella DATA_DIR se non riesci a leggere/scrivere i file.
- Controlla log in console/terminal per eccezioni sul parsing JSON.
- Se l'interfaccia web mostra dati mancanti, conferma che cars.json e appointments.json siano ben formati.

Licenza
-------
Il repository include una LICENSE (es. Apache-2.0). Verifica il file LICENSE nel repo per i dettagli.

Contribuire
----------
Aggiunte e correzioni sono benvenute:
- crea una branch feature/fix, fai commit chiari, apri una pull request descrivendo i cambiamenti.
- prima di aprire PR, prova l'app localmente e assicurati che non ci siano errori nelle rotte principali.

Contatti
--------
Per domande sul codice o richieste specifiche: puoi aprire un issue sul repository.

---
