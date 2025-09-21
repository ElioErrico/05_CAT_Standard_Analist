# ---------- prompt_helper.py ----------    

PROMPT_STD_ANALYSIS ="""Assumi il ruolo di progettista. Analizza il testo normativo fornito, segmentandolo in modo sistematico per garantire la tracciabilità e la completezza dei requisiti.
## Task

    Analizza esclusivamente il testo normativo fornito, suddividendo ogni capitolo/paragrafo in un numero congruo di segmenti per garantire una tracciabilità puntuale e non ridondante.
    Per ogni segmento, popola un oggetto JSON secondo lo schema fornito, senza aggiungere testo extra, commenti, formattazioni o codifiche markdown.
    Compila rigorosamente i seguenti campi per ogni riga:
        “Chapter/Paragraph No.”
        “Chapter/Paragraph Title”
        “Requirement/Standard Description”
        “Required Data / Configuration”
        “Regulatory References”
    Segui le regole di compilazione dettagliate per ogni campo (vedi sezione Vincoli).
    Lascia eventuali campi non applicabili come stringa vuota (“”).

## Vincoli

    - Output esclusivamente in formato JSON valido, conforme allo schema fornito.
    - Nessun testo aggiuntivo, nessun commento, nessun markdown, nessuna intestazione o code-fence.
    - Il campo “Requirement/Standard Description” deve contenere il testo originale della norma, senza alcuna modifica, sintesi, parafrasi o traduzione.
    - Segmenta i paragrafi lunghi in più righe, riportando per ciascuna riga la porzione esatta di testo corrispondente, per massimizzare la tracciabilità.
    - Il campo "Chapter/Paragraph No." deve contenere il numero/codice del capitolo/paragrafo deducibile dall’estratto, inserire un identificativo univoco o lasciarlo vuoto solo se impossibile.
    - Per "Required Data / Configuration", inserisci solo se strettamente necessario (dati, prove, configurazioni minime richieste dal paragrafo); altrimenti lascia vuoto.
    - Per "Regulatory References", elenca tutti i riferimenti espliciti (clausole, allegati, altre norme), lasciando vuoto se assenti.
    - Non inserire dati progettuali, valutazioni, interpretazioni, note personali o informazioni non presenti nel testo normativo fornito.
    - Se nell’analisi del testo normativo vengono individuate tabelle o formule, non riportare il loro contenuto dettagliato nelle righe del JSON. Limìtati a citarle (“Tabella X” o “Formula Y”) dove sono richiamate all’interno del testo, senza descriverne o trascriverne i dettagli nelle righe.

## Formato dell’output

Restituisci solo un oggetto JSON conforme al seguente schema (nessun testo extra):

{
  "rows": [
    {
      "Chapter/Paragraph No.": "",
      "Chapter/Paragraph Title": "",
      "Requirement/Standard Description": "",
      "Required Data / Configuration": "",
      "Regulatory References": ""
    }
    // ... (una riga per ciascun requisito/segmento)
  ]
}

## Best Practice

    - Segmenta i paragrafi lunghi in più righe, mantenendo la massima fedeltà al testo originario per ogni porzione.
    - Utilizza sempre la numerazione ufficiale e i titoli originali.

## Esempio di output atteso

{
  "rows": [
    {
      "Chapter/Paragraph No.": "6.4.1",
      "Chapter/Paragraph Title": "Electrical requirements",
      "Requirement/Standard Description": "The appliance shall be constructed so that live parts are not accessible, ...",
      "Required Data / Configuration": "",
      "Regulatory References": ""
    },
    {
      "Chapter/Paragraph No.": "6.4.1",
      "Chapter/Paragraph Title": "Electrical requirements",
      "Requirement/Standard Description": "Compliance is checked by inspection and by the test of 8.1, ...",
      "Required Data / Configuration": "Test method as per 8.1",
      "Regulatory References": "8.1"
    }
  ]

## Ultima riga generata:
L'ultima riga che hai inserito è: 

}"""