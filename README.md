## Istruzioni operative d'uso

### Creazione di un nuovo sito
 - Si proceda a creare un nuovo repositori usando lo starter del template [**Chirpy starter**](https://github.com/new?template_name=chirpy-starter&template_owner=cotes2020)
 - Il nome del repositori deve essere <username>.github.io
 - Creato il repository, si proceda, all'interno del repository in Settings > Pages > Build and Deployment e si selezioni dal menù a tendina la voce GitHub Actions.

### Configurazione del sito
 - Configurare il file `_config.yml` con i dati relativi al sito:
   - Timezone: Europe/Rome
   - Url: `https://<username>.github.io`
   - Modificare altri campi come nome, descrizione, ecc.

### Utilizzo dello script e creazione di post
  - Lo script "softlab-builder", correttamente configurato, permette di gestire la creazione
di nuovi post in maniera semplice. Basta creare un progetto dotato di `README.md` nell'account
github di softlab-unimore.
  - C'è la possibilità di creare un nuovo post in maniera autonoma. Si raccomanda di seguire le 
istruzioni riportate nella [guida del template](https://chirpy.cotes.page/posts/write-a-new-post/)

### Configurazione dello script
 - Al primo avvio, si fornisca:
    - Nome utente github
    - Token di accesso di GitHub (generabile da [qui](https://github.com/settings/tokens))
    - Token API di OpenAI (generabile da [qui](https://platform.openai.com/api-keys))
      - **Warning**:
       Si presti attenzione al plan di OpenAI. Le richieste all'API hanno un costo in base ai token utilizzati.
       Con un credito di 5$ si possono effettuare circa PIù di 5000 richieste all'API che corrispondono a 5000 
       aggiornamenti dei readme. Se si suppone di aggiornare un README con una media di 1 aggiornamento ogni 2
       giorni, il credito di 5$ dovrebbe essere sufficiente per circa 10.000 giorni, ovvero 27 anni.
