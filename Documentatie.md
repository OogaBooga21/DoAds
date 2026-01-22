# DoAds Lead Generator - Manual de Utilizare

Bun venit la DoAds Lead Generator! Acest manual vă va ghida prin funcționalitățile aplicației și vă va ajuta să o utilizați eficient.

![Dashboard Principal](placeholder_dashboard.png "O captură de ecran a dashboard-ului principal")

## Cuprins

1.  [Introducere](#introducere)
2.  [Primii Pași](#primii-pași)
    *   [Înregistrare](#înregistrare)
    *   [Autentificare](#autentificare)
3.  [Dashboard Principal](#dashboard-principal)
    *   [Navigare](#navigare)
4.  [Funcționalități](#funcționalități)
    *   [Instrumentul de Scraper (Generare de Lead-uri cu AI)](#instrumentul-de-scraper-generare-de-lead-uri-cu-ai)
    *   [Instrumentul "Mail to Lead"](#instrumentul-mail-to-lead)
    *   [Generator de Oferte Automate](#generator-de-oferte-automate)
    *   [Creare Manuală de Lead-uri](#creare-manuală-de-lead-uri)
5.  [Gestionarea Datelor](#gestionarea-datelor)
    *   [Pagina "Sarcinile Mele"](#pagina-sarcinile-mele)
    *   [Pagina "Emailuri"](#pagina-emailuri)
6.  [Depanare](#depanare)

---

## 1. Introducere

DoAds Lead Generator este un instrument puternic conceput pentru a eficientiza procesul de generare de lead-uri. Vă ajută să găsiți potențiali clienți, să colectați informații despre aceștia și să generați emailuri personalizate de contact pentru a demara procesul de vânzare.

## 2. Primii Pași

### Înregistrare

Pentru a începe să utilizați aplicația, trebuie să vă creați un cont.

1.  Navigați la pagina de înregistrare.
2.  Introduceți adresa de email și alegeți o parolă sigură.
3.  Faceți clic pe butonul "Înregistrare".

![Pagina de Înregistrare](placeholder_register.png "O captură de ecran a paginii de înregistrare")

### Autentificare

După ce aveți un cont, vă puteți autentifica:

1.  Navigați la pagina de autentificare.
2.  Introduceți emailul și parola înregistrate.
3.  Faceți clic pe butonul "Autentificare".

![Pagina de Autentificare](placeholder_login.png "O captură de ecran a paginii de autentificare")

---

## 3. Dashboard Principal

După autentificare, veți fi direcționat către dashboard-ul principal. Aici puteți accesa toate instrumentele de generare de lead-uri.

### Navigare

Antetul conține linkurile principale de navigare:

*   **Acasă:** Vă duce la dashboard-ul principal cu instrumentele de generare de lead-uri.
*   **Sarcinile Mele:** Afișează un istoric al tuturor sarcinilor de generare de lead-uri pe care le-ați rulat.
*   **Emailuri:** Afișează o listă cu toate emailurile pe care le-ați trimis prin intermediul aplicației.

![Antetul de Navigare](placeholder_navigation.png "O captură de ecran a antetului de navigare")

---

## 4. Funcționalități

Dashboard-ul principal este organizat în file (tab-uri), fiecare oferind un instrument specific.

### Instrumentul de Scraper (Generare de Lead-uri cu AI)

Acesta este instrumentul principal pentru găsirea de noi lead-uri de pe Google Maps.

![Formularul Instrumentului de Scraper](placeholder_scrape_tool.png "O captură de ecran a formularului instrumentului de scraper")

**Cum se Utilizează:**

1.  **Interogare Google Maps:** Introduceți o interogare de căutare așa cum ați face pe Google Maps (ex: "instalatori în București", "agenții de web design în Cluj-Napoca").
2.  **Număr Maxim de Rezultate:** Specificați numărul maxim de rezultate pe care doriți să le extrageți de pe Google Maps (până la 50).
3.  **Oferta Dumneavoastră:** Descrieți clar produsul sau serviciul pe care îl oferiți. Acest lucru este crucial pentru generarea unui email relevant.
4.  **Tonul Emailului:** Definiți tonul dorit pentru emailul generat (ex: "Formal și profesional", "Prietenos și informal").
5.  **Instrucțiuni Suplimentare (Opțional):** Furnizați orice detalii suplimentare pe care doriți ca AI-ul să le includă în email (ex: "Menționați cei 10 ani de experiență", "Evidențiați consultanța noastră gratuită").
6.  **Limba Promptului:** Alegeți limba pentru promptul AI (Engleză sau Română). Aceasta influențează limba emailului generat.
7.  Faceți clic pe **"Generează și Descarcă JSON"**.

**Ce Face:**

*   Sistemul caută pe Google Maps cu interogarea dumneavoastră.
*   Vizitează site-ul web al fiecărui rezultat pentru a găsi informații de contact și a înțelege afacerea.
*   Utilizează aceste informații și detaliile ofertei dumneavoastră pentru a genera un email personalizat de contact pentru fiecare lead.
*   O nouă sarcină este creată, și veți fi redirecționat către pagina "Sarcinile Mele" pentru a vedea progresul.

### Instrumentul "Mail to Lead"

Utilizați acest instrument atunci când aveți deja o listă de adrese de email și doriți să găsiți site-urile web ale companiilor respective și să generați emailuri personalizate.

![Formularul Instrumentului Mail to Lead](placeholder_mail_to_lead_tool.png "O captură de ecran a formularului instrumentului Mail to Lead")

**Cum se Utilizează:**

1.  **Listă de Emailuri:** Încărcați un fișier `.txt` care conține o listă de adrese de email, câte o adresă pe fiecare rând.
2.  Completați câmpurile **Oferta Dumneavoastră**, **Tonul Emailului**, **Instrucțiuni Suplimentare** și **Limba Promptului**, la fel ca în Instrumentul de Scraper.
3.  Faceți clic pe **"Găsește Site-uri Web și Generează Emailuri"**.

**Ce Face:**

*   Pentru fiecare email, instrumentul încearcă să găsească site-ul web al companiei asociate.
*   Apoi, extrage informații de pe site și generează un email personalizat bazat pe oferta dumneavoastră.
*   O nouă sarcină este creată pe pagina "Sarcinile Mele".

### Generator de Oferte Automate

Acest instrument vă ajută să creați rapid un rezumat al serviciilor unei companii pe baza site-ului său web.

![Formularul Generatorului de Oferte Automate](placeholder_auto_offer_generator.png "O captură de ecran a formularului generatorului de oferte automate")

**Cum se Utilizează:**

1.  **URL Site Web:** Introduceți URL-ul complet al site-ului web al companiei (ex: `https://exemplu.com`).
2.  **Informații Suplimentare (Opțional):** Adăugați orice context sau detalii specifice pe care doriți să le includeți în rezumat.
3.  Faceți clic pe **"Generează Rezumatul Ofertei"**.

**Ce Face:**

*   Instrumentul extrage informații de pe site-ul web furnizat.
*   Generează un rezumat concis al ofertelor companiei.
*   Rezultatul este afișat pe pagină și îl puteți copia cu ușurință.

### Creare Manuală de Lead-uri

Această funcționalitate vă permite să creați un lead manual, ceea ce este util pentru testare sau pentru lead-uri care nu pot fi găsite prin extragere automată.

![Formularul de Creare Manuală de Lead-uri](placeholder_manual_lead_creation.png "O captură de ecran a formularului de creare manuală de lead-uri")

**Cum se Utilizează:**

1.  **Nume Companie:** Introduceți numele companiei.
2.  **Email Contact:** Introduceți adresa de email a lead-ului.
3.  **URL Site Web:** Introduceți URL-ul site-ului web al companiei.
4.  Completați câmpurile **Oferta Dumneavoastră**, **Tonul Emailului**, **Instrucțiuni Suplimentare** și **Limba Promptului**.
5.  Faceți clic pe **"Creează Lead și Generează Email"**.

**Ce Face:**

*   Creează un nou lead și o sarcină corespunzătoare.
*   Generează un email personalizat pe baza informațiilor furnizate.

---

## 5. Gestionarea Datelor

### Pagina "Sarcinile Mele"

Această pagină listează toate sarcinile pe care le-ați inițiat.

![Pagina Sarcinile Mele](placeholder_my_tasks_page.png "O captură de ecran a paginii Sarcinile Mele")

**Coloane:**

*   **ID:** Identificatorul unic pentru sarcină.
*   **Status:** Starea curentă a sarcinii:
    *   `PENDING`: Sarcina așteaptă să fie procesată.
    *   `RUNNING`: Sarcina este în curs de desfășurare.
    *   `SUCCESS`: Sarcina a fost finalizată cu succes.
    *   `FAILURE`: Sarcina a eșuat.
*   **Tip:** Tipul de sarcină care a fost rulată (Google Maps, Mail to Lead, etc.).
*   **Interogare:** Interogarea de căutare sau intrarea pe care ați furnizat-o.
*   **Limbă:** Limba promptului utilizată.
*   **Creat La:** Data și ora la care a fost creată sarcina.
*   **Acțiuni:** Acțiuni disponibile pentru sarcină (doar pentru statusul `SUCCESS`).

**Acțiuni pentru Sarcinile Finalizate cu Succes:**

*   **Arată Lead-uri:** Deschide o fereastră pop-up care afișează lead-urile găsite de sarcină (numele companiei, site-ul web și emailul de contact).
*   **Descarcă:** Descarcă rezultatul complet al sarcinii ca fișier JSON, care include emailurile generate.
*   **Auto-Mail:** Trimite automat emailurile generate către toate lead-urile găsite în sarcină.
*   **Manual-Mail:** Deschide un modal unde puteți revizui fiecare email generat și le puteți trimite individual.

### Pagina "Emailuri"

Această pagină afișează o listă cuprinzătoare a tuturor emailurilor pe care le-ați trimis.

![Pagina Emailuri](placeholder_emails_page.png "O captură de ecran a paginii Emailuri")

**Coloane:**

*   **Destinatar:** Adresa de email a persoanei pe care ați contactat-o.
*   **Subiect:** Linia de subiect a emailului.
*   **Status:** Starea de livrare a emailului, urmărită prin webhook-uri:
    *   `SENT`: Emailul a fost trimis.
    *   `DELIVERED`: Emailul a fost livrat cu succes către serverul de mail al destinatarului.
    *   `OPENED`: Destinatarul a deschis emailul.
    *   `CLICKED`: Destinatarul a făcut clic pe un link din email.
    *   `REPLIED`: Destinatarul a răspuns la emailul dumneavoastră.
    *   `FAILED`: Emailul nu a putut fi livrat.
*   **Trimis La:** Data și ora la care a fost trimis emailul.
*   **Acțiuni:**
    *   **Arată Relaționate:** Vă duce la o pagină care afișează întreaga conversație prin email cu acel destinatar, inclusiv emailul dumneavoastră original și răspunsurile acestuia.

---

## 6. Depanare

Atunci când ceva nu funcționează conform așteptărilor, furnizarea de informații detaliate poate ajuta dezvoltatorul să diagnosticheze problema. Iată cum să colectați informații relevante:

### Pentru Toate Problemele

1.  **Descrieți Pașii:** Notați pașii exacți pe care i-ați urmat și care au dus la eroare. De exemplu:
    *   "Am mers la Instrumentul de Scraper."
    *   "Am introdus 'dulgheri în Brașov' ca interogare."
    *   "Am făcut clic pe 'Generează și Descarcă JSON'."
    *   "Pagina a afișat un mesaj de eroare."
2.  **ID Sarcină:** Dacă problema este legată de o anumită sarcină, mergeți la pagina "Sarcinile Mele" și găsiți **ID-ul Sarcinii**. Aceasta este cea mai importantă informație pentru depanare.
3.  **Capturi de Ecran:** Faceți o captură de ecran a întregului ecran, inclusiv a oricăror mesaje de eroare.

### Erori în Consola Browserului

Uneori, erorile sunt afișate în consola de dezvoltator a browserului.

**Cum se Deschide Consola:**

*   **Chrome/Edge:** Faceți clic dreapta pe pagină, selectați "Inspectați", apoi faceți clic pe fila "Consolă".
*   **Firefox:** Faceți clic dreapta pe pagină, selectați "Inspectați Elementul", apoi faceți clic pe fila "Consolă".

**Ce să Căutați:**

*   Căutați orice mesaje scrise cu roșu. Acestea sunt de obicei erori.
*   Copiați și lipiți textul complet al mesajelor de eroare.
*   Faceți o captură de ecran a consolei cu erorile vizibile.

Prin furnizarea ID-ului sarcinii, a unei descrieri a pașilor și a oricăror erori din consolă, puteți ajuta echipa de dezvoltare să rezolve problemele mult mai rapid.
