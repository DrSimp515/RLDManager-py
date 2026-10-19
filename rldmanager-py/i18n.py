import locale
from typing import Literal, Optional

Lang = Literal["en", "es", "pt", "pt_br", "fr", "it", "de", "ru"]

_STRINGS: dict[str, dict[Lang, str]] = {
    "app_title":            {"en": "RLD Manager", "es": "RLD Manager", "pt": "RLD Manager", "pt_br": "RLD Manager", "fr": "RLD Manager", "it": "RLD Manager", "de": "RLD Manager", "ru": "RLD Manager"},
    "window_title_file":    {"en": "RLD Manager — {filename}", "es": "RLD Manager — {filename}", "pt": "RLD Manager — {filename}", "pt_br": "RLD Manager — {filename}", "fr": "RLD Manager — {filename}", "it": "RLD Manager — {filename}", "de": "RLD Manager — {filename}", "ru": "RLD Manager — {filename}"},
    "window_title_id":      {"en": "ID: {id}  |  Speaker: {speaker}", "es": "ID: {id}  |  Hablante: {speaker}", "pt": "ID: {id}  |  Orador: {speaker}", "pt_br": "ID: {id}  |  Falante: {speaker}", "fr": "ID : {id}  |  Locuteur : {speaker}", "it": "ID: {id}  |  Oratore: {speaker}", "de": "ID: {id}  |  Sprecher: {speaker}", "ru": "ID: {id}  |  Говорящий: {speaker}"},

    "menu_file":            {"en": "File", "es": "Archivo", "pt": "Ficheiro", "pt_br": "Arquivo", "fr": "Fichier", "it": "File", "de": "Datei", "ru": "Файл"},
    "menu_open":            {"en": "Open", "es": "Abrir", "pt": "Abrir", "pt_br": "Abrir", "fr": "Ouvrir", "it": "Apri", "de": "Öffnen", "ru": "Открыть"},
    "menu_save":            {"en": "Save As", "es": "Guardar como", "pt": "Guardar como", "pt_br": "Salvar como", "fr": "Enregistrer sous", "it": "Salva con nome", "de": "Speichern unter", "ru": "Сохранить как"},
    "menu_save_all":        {"en": "Save All", "es": "Guardar todo", "pt": "Guardar tudo", "pt_br": "Salvar tudo", "fr": "Tout enregistrer", "it": "Salva tutto", "de": "Alles speichern", "ru": "Сохранить всё"},
    "menu_tools":           {"en": "Tools", "es": "Herramientas", "pt": "Ferramentas", "pt_br": "Ferramentas", "fr": "Outils", "it": "Strumenti", "de": "Werkzeuge", "ru": "Инструменты"},
    "menu_export_text":     {"en": "Export Text…", "es": "Exportar texto…", "pt": "Exportar texto…", "pt_br": "Exportar texto…", "fr": "Exporter le texte…", "it": "Esporta testo…", "de": "Text exportieren…", "ru": "Экспорт текста…"},
    "menu_export_plain":    {"en": "Export Plain Text…", "es": "Exportar texto plano…", "pt": "Exportar texto simples…", "pt_br": "Exportar texto simples…", "fr": "Exporter le texte brut…", "it": "Esporta testo semplice…", "de": "Klartext exportieren…", "ru": "Экспорт обычного текста…"},
    "menu_import_text":     {"en": "Import Text (Reinsert)…", "es": "Importar texto (Reinsertar)…", "pt": "Importar texto (Reinserir)…", "pt_br": "Importar texto (Reinserir)…", "fr": "Importer le texte (Réinsérer)…", "it": "Importa testo (Reinserisci)…", "de": "Text importieren (Wiedereinfügen)…", "ru": "Импорт текста (Вставка)…"},
    "menu_find_key":        {"en": "Find Key", "es": "Buscar clave", "pt": "Procurar chave", "pt_br": "Buscar chave", "fr": "Chercher la clé", "it": "Cerca chiave", "de": "Schlüssel suchen", "ru": "Найти ключ"},
    "menu_crypt":           {"en": "Crypt / Decrypt", "es": "Cifrar / Descifrar", "pt": "Cifrar / Decifrar", "pt_br": "Cifrar / Decifrar", "fr": "Chiffrer / Déchiffrer", "it": "Cifra / Decifra", "de": "Verschlüsseln / Entschlüsseln", "ru": "Шифровать / Расшифровать"},
    "menu_settings":        {"en": "Settings", "es": "Ajustes", "pt": "Definições", "pt_br": "Configurações", "fr": "Paramètres", "it": "Impostazioni", "de": "Einstellungen", "ru": "Настройки"},
    "menu_theme":           {"en": "Theme", "es": "Tema", "pt": "Tema", "pt_br": "Tema", "fr": "Thème", "it": "Tema", "de": "Design", "ru": "Тема"},
    "menu_language":        {"en": "Language", "es": "Idioma", "pt": "Idioma", "pt_br": "Idioma", "fr": "Langue", "it": "Lingua", "de": "Sprache", "ru": "Язык"},
    "menu_open_multiple":   {"en": "Open Multiple…", "es": "Abrir varios…", "pt": "Abrir vários…", "pt_br": "Abrir vários…", "fr": "Ouvrir plusieurs…", "it": "Apri multipli…", "de": "Mehrere öffnen…", "ru": "Открыть несколько…"},
    "menu_help":            {"en": "Help", "es": "Ayuda", "pt": "Ajuda", "pt_br": "Ajuda", "fr": "Aide", "it": "Aiuto", "de": "Hilfe", "ru": "Справка"},
    "menu_about":           {"en": "About…", "es": "Acerca de…", "pt": "Sobre…", "pt_br": "Sobre…", "fr": "À propos…", "it": "Informazioni…", "de": "Über…", "ru": "О программе…"},

    "col_index":            {"en": "#", "es": "#", "pt": "#", "pt_br": "#", "fr": "#", "it": "#", "de": "#", "ru": "#"},
    "col_file":             {"en": "File", "es": "Archivo", "pt": "Ficheiro", "pt_br": "Arquivo", "fr": "Fichier", "it": "File", "de": "Datei", "ru": "Файл"},
    "col_speaker":          {"en": "Speaker", "es": "Hablante", "pt": "Orador", "pt_br": "Falante", "fr": "Locuteur", "it": "Oratore", "de": "Sprecher", "ru": "Говорящий"},
    "col_dialogue":         {"en": "Dialogue", "es": "Diálogo", "pt": "Diálogo", "pt_br": "Diálogo", "fr": "Dialogue", "it": "Dialogo", "de": "Dialog", "ru": "Диалог"},

    "dlg_open_title":       {"en": "Open script…", "es": "Abrir script…", "pt": "Abrir script…", "pt_br": "Abrir script…", "fr": "Ouvrir un script…", "it": "Apri script…", "de": "Skript öffnen…", "ru": "Открыть скрипт…"},
    "dlg_save_title":       {"en": "Save script as…", "es": "Guardar script como…", "pt": "Guardar script como…", "pt_br": "Salvar script como…", "fr": "Enregistrer le script sous…", "it": "Salva script come…", "de": "Skript speichern unter…", "ru": "Сохранить скрипт как…"},
    "dlg_filter":           {"en": "ExHIBIT Script (*.rld)", "es": "Script ExHIBIT (*.rld)", "pt": "Script ExHIBIT (*.rld)", "pt_br": "Script ExHIBIT (*.rld)", "fr": "Script ExHIBIT (*.rld)", "it": "Script ExHIBIT (*.rld)", "de": "ExHIBIT-Skript (*.rld)", "ru": "Скрипт ExHIBIT (*.rld)"},
    "dlg_saved":            {"en": "File saved.", "es": "Archivo guardado.", "pt": "Ficheiro guardado.", "pt_br": "Arquivo salvo.", "fr": "Fichier enregistré.", "it": "File salvato.", "de": "Datei gespeichert.", "ru": "Файл сохранён."},
    "dlg_done":             {"en": "Done!", "es": "¡Listo!", "pt": "Concluído!", "pt_br": "Concluído!", "fr": "Terminé !", "it": "Fatto!", "de": "Fertig!", "ru": "Готово!"},
    "dlg_error":            {"en": "Error", "es": "Error", "pt": "Erro", "pt_br": "Erro", "fr": "Erreur", "it": "Errore", "de": "Fehler", "ru": "Ошибка"},
    "dlg_key_not_found":    {"en": "Failed to find key.", "es": "No se encontró la clave.", "pt": "Não foi possível encontrar a chave.", "pt_br": "Não foi possível encontrar a chave.", "fr": "Impossible de trouver la clé.", "it": "Impossibile trovare la chiave.", "de": "Schlüssel nicht gefunden.", "ru": "Не удалось найти ключ."},
    "dlg_key_found":        {"en": "Key found: 0x{key}\nSaved to RLDKeys.txt. Try opening the script now.", "es": "Clave encontrada: 0x{key}\nGuardada en RLDKeys.txt. Intenta abrir el script ahora.", "pt": "Chave encontrada: 0x{key}\nGuardada em RLDKeys.txt. Tente abrir o script agora.", "pt_br": "Chave encontrada: 0x{key}\nSalva em RLDKeys.txt. Tente abrir o script agora.", "fr": "Clé trouvée : 0x{key}\nEnregistrée dans RLDKeys.txt. Essayez d'ouvrir le script maintenant.", "it": "Chiave trovata: 0x{key}\nSalvata in RLDKeys.txt. Prova ad aprire lo script ora.", "de": "Schlüssel gefunden: 0x{key}\nIn RLDKeys.txt gespeichert. Versuchen Sie, das Skript jetzt zu öffnen.", "ru": "Ключ найден: 0x{key}\nСохранён в RLDKeys.txt. Попробуйте открыть скрипт сейчас."},
    "dlg_brute_warn":       {"en": "Brute-force search — may take 2–3 hours.\nHigh CPU usage expected.", "es": "Búsqueda por fuerza bruta — puede tardar 2-3 horas.\nSe espera uso intensivo de CPU.", "pt": "Pesquisa por força bruta — pode demorar 2–3 horas.\nEsperado uso intensivo de CPU.", "pt_br": "Busca por força bruta — pode levar 2–3 horas.\nUso intensivo de CPU esperado.", "fr": "Recherche par force brute — peut prendre 2 à 3 heures.\nUtilisation élevée du CPU attendue.", "it": "Ricerca forza bruta — può richiedere 2–3 ore.\nUso elevato della CPU previsto.", "de": "Brute-Force-Suche — kann 2–3 Stunden dauern.\nHohe CPU-Auslastung erwartet.", "ru": "Поиск перебором — может занять 2–3 часа.\nОжидается высокая нагрузка на CPU."},
    "dlg_select_game":      {"en": "Select a game", "es": "Seleccionar juego", "pt": "Selecionar jogo", "pt_br": "Selecionar jogo", "fr": "Sélectionner un jeu", "it": "Seleziona un gioco", "de": "Spiel auswählen", "ru": "Выберите игру"},
    "dlg_key_label":        {"en": "Key:", "es": "Clave:", "pt": "Chave:", "pt_br": "Chave:", "fr": "Clé :", "it": "Chiave:", "de": "Schlüssel:", "ru": "Ключ:"},
    "dlg_other":            {"en": "Other…", "es": "Otro…", "pt": "Outro…", "pt_br": "Outro…", "fr": "Autre…", "it": "Altro…", "de": "Andere…", "ru": "Другое…"},
    "dlg_confirm":          {"en": "Confirm", "es": "Confirmar", "pt": "Confirmar", "pt_br": "Confirmar", "fr": "Confirmer", "it": "Conferma", "de": "Bestätigen", "ru": "Подтвердить"},
    "dlg_cancel":           {"en": "Cancel", "es": "Cancelar", "pt": "Cancelar", "pt_br": "Cancelar", "fr": "Annuler", "it": "Annulla", "de": "Abbrechen", "ru": "Отмена"},
    "dlg_export_title":     {"en": "Save text export…", "es": "Guardar exportación de texto…", "pt": "Guardar exportação de texto…", "pt_br": "Salvar exportação de texto…", "fr": "Enregistrer l'exportation de texte…", "it": "Salva esportazione testo…", "de": "Textexport speichern…", "ru": "Сохранить экспорт текста…"},
    "dlg_import_title":     {"en": "Open text file to import…", "es": "Abrir archivo de texto a importar…", "pt": "Abrir ficheiro de texto a importar…", "pt_br": "Abrir arquivo de texto a importar…", "fr": "Ouvrir le fichier texte à importer…", "it": "Apri file di testo da importare…", "de": "Textdatei zum Importieren öffnen…", "ru": "Открыть текстовый файл для импорта…"},
    "dlg_txt_filter":       {"en": "Text files (*.txt)", "es": "Archivos de texto (*.txt)", "pt": "Ficheiros de texto (*.txt)", "pt_br": "Arquivos de texto (*.txt)", "fr": "Fichiers texte (*.txt)", "it": "File di testo (*.txt)", "de": "Textdateien (*.txt)", "ru": "Текстовые файлы (*.txt)"},
    "dlg_imported":         {"en": "Imported {n} translations.", "es": "Importadas {n} traducciones.", "pt": "Importadas {n} traduções.", "pt_br": "Importadas {n} traduções.", "fr": "{n} traductions importées.", "it": "{n} traduzioni importate.", "de": "{n} Übersetzungen importiert.", "ru": "Импортировано переводов: {n}."},
    "dlg_no_match":         {"en": "No matching entries found in this file.", "es": "No se encontraron entradas coincidentes en este archivo.", "pt": "Não foram encontradas entradas correspondentes neste ficheiro.", "pt_br": "Nenhuma entrada correspondente encontrada neste arquivo.", "fr": "Aucune entrée correspondante trouvée dans ce fichier.", "it": "Nessuna voce corrispondente trovata in questo file.", "de": "Keine passenden Einträge in dieser Datei gefunden.", "ru": "Подходящие записи в этом файле не найдены."},
    "dlg_save_all_title":   {"en": "Choose destination folder", "es": "Elegir carpeta de destino", "pt": "Escolher pasta de destino", "pt_br": "Escolher pasta de destino", "fr": "Choisir le dossier de destination", "it": "Scegli cartella di destinazione", "de": "Zielordner wählen", "ru": "Выберите папку назначения"},
    "dlg_saved_all":        {"en": "Saved {n} file(s).", "es": "{n} archivo(s) guardado(s).", "pt": "Guardado(s) {n} ficheiro(s).", "pt_br": "{n} arquivo(s) salvo(s).", "fr": "{n} fichier(s) enregistré(s).", "it": "{n} file salvato/i.", "de": "{n} Datei(en) gespeichert.", "ru": "Сохранено файлов: {n}."},
    "dlg_export_plain_title":{"en": "Save plain-text export…", "es": "Guardar exportación de texto plano…", "pt": "Guardar exportação de texto simples…", "pt_br": "Salvar exportação de texto simples…", "fr": "Enregistrer l'exportation de texte brut…", "it": "Salva esportazione testo semplice…", "de": "Klartextexport speichern…", "ru": "Сохранить экспорт обычного текста…"},
    "dlg_crypt_title":      {"en": "Crypt / Decrypt script", "es": "Cifrar / Descifrar script", "pt": "Cifrar / Decifrar script", "pt_br": "Cifrar / Decifrar script", "fr": "Chiffrer / Déchiffrer le script", "it": "Cifra / Decifra script", "de": "Skript verschlüsseln / entschlüsseln", "ru": "Шифрование / расшифровка скрипта"},
    "dlg_key_select_title": {"en": "Select encryption key", "es": "Seleccionar clave de cifrado", "pt": "Selecionar chave de cifra", "pt_br": "Selecionar chave de cifragem", "fr": "Sélectionner la clé de chiffrement", "it": "Seleziona chiave di cifratura", "de": "Verschlüsselungsschlüssel auswählen", "ru": "Выберите ключ шифрования"},
    "dlg_no_tabs":          {"en": "No scripts loaded.", "es": "No hay scripts cargados.", "pt": "Nenhum script carregado.", "pt_br": "Nenhum script carregado.", "fr": "Aucun script chargé.", "it": "Nessuno script caricato.", "de": "Keine Skripte geladen.", "ru": "Скрипты не загружены."},
    "dlg_confirm_discard":  {"en": "Discard unsaved changes?", "es": "¿Descartar cambios sin guardar?", "pt": "Descartar alterações não guardadas?", "pt_br": "Descartar alterações não salvas?", "fr": "Annuler les modifications non enregistrées ?", "it": "Scartare le modifiche non salvate?", "de": "Ungespeicherte Änderungen verwerfen?", "ru": "Отменить несохранённые изменения?"},

    "status_ready":         {"en": "Ready", "es": "Listo", "pt": "Pronto", "pt_br": "Pronto", "fr": "Prêt", "it": "Pronto", "de": "Bereit", "ru": "Готово"},
    "status_loaded":        {"en": "Loaded {n} strings", "es": "Cargadas {n} cadenas", "pt": "Carregadas {n} cadeias", "pt_br": "Carregadas {n} strings", "fr": "{n} chaînes chargées", "it": "{n} stringhe caricate", "de": "{n} Zeichenketten geladen", "ru": "Загружено строк: {n}"},
    "status_files":         {"en": "{n} file(s) loaded", "es": "{n} archivo(s) cargado(s)", "pt": "{n} ficheiro(s) carregado(s)", "pt_br": "{n} arquivo(s) carregado(s)", "fr": "{n} fichier(s) chargé(s)", "it": "{n} file caricato/i", "de": "{n} Datei(en) geladen", "ru": "Загружено файлов: {n}"},
    "status_loading":       {"en": "Loading {n} file(s)…", "es": "Cargando {n} archivo(s)…", "pt": "A carregar {n} ficheiro(s)…", "pt_br": "Carregando {n} arquivo(s)…", "fr": "Chargement de {n} fichier(s)…", "it": "Caricamento di {n} file…", "de": "Lade {n} Datei(en)…", "ru": "Загрузка файлов: {n}…"},
    "status_loading_file":  {"en": "Loading {name}…", "es": "Cargando {name}…", "pt": "A carregar {name}…", "pt_br": "Carregando {name}…", "fr": "Chargement de {name}…", "it": "Caricamento di {name}…", "de": "Lade {name}…", "ru": "Загрузка {name}…"},
    "status_loaded_file":   {"en": "Loaded {name} ({n} strings)", "es": "Cargado {name} ({n} cadenas)", "pt": "Carregado {name} ({n} cadeias)", "pt_br": "Carregado {name} ({n} strings)", "fr": "{name} chargé ({n} chaînes)", "it": "{name} caricato ({n} stringhe)", "de": "{name} geladen ({n} Zeichenketten)", "ru": "{name} загружен ({n} строк)"},
    "status_saving":        {"en": "Saving {done}/{total}…", "es": "Guardando {done}/{total}…", "pt": "A guardar {done}/{total}…", "pt_br": "Salvando {done}/{total}…", "fr": "Enregistrement {done}/{total}…", "it": "Salvataggio {done}/{total}…", "de": "Speichere {done}/{total}…", "ru": "Сохранение {done}/{total}…"},
    "status_searching":     {"en": "Searching… {pct}% ({rem} remaining)", "es": "Buscando… {pct}% ({rem} restantes)", "pt": "A pesquisar… {pct}% ({rem} restantes)", "pt_br": "Buscando… {pct}% ({rem} restantes)", "fr": "Recherche… {pct}% ({rem} restants)", "it": "Ricerca… {pct}% ({rem} rimanenti)", "de": "Suche… {pct}% ({rem} verbleibend)", "ru": "Поиск… {pct}% (осталось {rem})"},
    "status_searching_keys":{"en": "Searching decryption key…", "es": "Buscando clave de descifrado…", "pt": "A procurar chave de decifra…", "pt_br": "Buscando chave de decifração…", "fr": "Recherche de la clé de déchiffrement…", "it": "Ricerca della chiave di decifratura…", "de": "Suche Entschlüsselungsschlüssel…", "ru": "Поиск ключа расшифровки…"},
    "status_stopping":      {"en": "Stopping…", "es": "Deteniendo…", "pt": "A parar…", "pt_br": "Parando…", "fr": "Arrêt…", "it": "Arresto…", "de": "Stoppe…", "ru": "Остановка…"},
    "status_exported":      {"en": "Export complete.", "es": "Exportación completa.", "pt": "Exportação concluída.", "pt_br": "Exportação concluída.", "fr": "Exportation terminée.", "it": "Esportazione completata.", "de": "Export abgeschlossen.", "ru": "Экспорт завершён."},
    "status_exported_plain":{"en": "Plain-text export complete.", "es": "Exportación de texto plano completa.", "pt": "Exportação de texto simples concluída.", "pt_br": "Exportação de texto simples concluída.", "fr": "Exportation de texte brut terminée.", "it": "Esportazione testo semplice completata.", "de": "Klartextexport abgeschlossen.", "ru": "Экспорт обычного текста завершён."},
    "status_crypt_done":    {"en": "Encrypted → {path}", "es": "Cifrado → {path}", "pt": "Cifrado → {path}", "pt_br": "Cifrado → {path}", "fr": "Chiffré → {path}", "it": "Cifrato → {path}", "de": "Verschlüsselt → {path}", "ru": "Зашифровано → {path}"},

    "edit_label":           {"en": "Edit (Enter to commit and advance)", "es": "Editar (Enter confirma y avanza)", "pt": "Editar (Enter confirma e avança)", "pt_br": "Editar (Enter confirma e avança)", "fr": "Éditer (Entrée pour valider et avancer)", "it": "Modifica (Invio per confermare e avanzare)", "de": "Bearbeiten (Eingabe bestätigt und weiter)", "ru": "Редактировать (Enter — подтвердить и перейти далее)"},
    "search_placeholder":   {"en": "Search…", "es": "Buscar…", "pt": "Pesquisar…", "pt_br": "Buscar…", "fr": "Rechercher…", "it": "Cerca…", "de": "Suchen…", "ru": "Поиск…"},
    "commit_next":          {"en": "Commit & Next", "es": "Confirmar y avanzar", "pt": "Confirmar e avançar", "pt_br": "Confirmar e avançar", "fr": "Valider et suivant", "it": "Conferma e avanti", "de": "Bestätigen und weiter", "ru": "Подтвердить и далее"},

    "theme_light":          {"en": "Light", "es": "Claro", "pt": "Claro", "pt_br": "Claro", "fr": "Clair", "it": "Chiaro", "de": "Hell", "ru": "Светлая"},
    "theme_dark":           {"en": "Dark", "es": "Oscuro", "pt": "Escuro", "pt_br": "Escuro", "fr": "Sombre", "it": "Scuro", "de": "Dunkel", "ru": "Тёмная"},
    "theme_system":         {"en": "System", "es": "Sistema", "pt": "Sistema", "pt_br": "Sistema", "fr": "Système", "it": "Sistema", "de": "System", "ru": "Системная"},

    "lang_en":              {"en": "English", "es": "English", "pt": "English", "pt_br": "English", "fr": "English", "it": "English", "de": "English", "ru": "English"},
    "lang_es":              {"en": "Español", "es": "Español", "pt": "Español", "pt_br": "Español", "fr": "Español", "it": "Español", "de": "Español", "ru": "Español"},
    "lang_pt":              {"en": "Português", "es": "Português", "pt": "Português", "pt_br": "Português", "fr": "Português", "it": "Português", "de": "Português", "ru": "Português"},
    "lang_pt_br":           {"en": "Português (Brasil)", "es": "Português (Brasil)", "pt": "Português (Brasil)", "pt_br": "Português (Brasil)", "fr": "Português (Brasil)", "it": "Português (Brasil)", "de": "Português (Brasil)", "ru": "Português (Brasil)"},
    "lang_fr":              {"en": "Français", "es": "Français", "pt": "Français", "pt_br": "Français", "fr": "Français", "it": "Français", "de": "Français", "ru": "Français"},
    "lang_it":              {"en": "Italiano", "es": "Italiano", "pt": "Italiano", "pt_br": "Italiano", "fr": "Italiano", "it": "Italiano", "de": "Italiano", "ru": "Italiano"},
    "lang_de":              {"en": "Deutsch", "es": "Deutsch", "pt": "Deutsch", "pt_br": "Deutsch", "fr": "Deutsch", "it": "Deutsch", "de": "Deutsch", "ru": "Deutsch"},
    "lang_ru":              {"en": "Русский", "es": "Русский", "pt": "Русский", "pt_br": "Русский", "fr": "Русский", "it": "Русский", "de": "Русский", "ru": "Русский"},

    "btn_stop_search":      {"en": "Stop search", "es": "Detener búsqueda", "pt": "Parar pesquisa", "pt_br": "Parar busca", "fr": "Arrêter la recherche", "it": "Ferma ricerca", "de": "Suche stoppen", "ru": "Остановить поиск"},

    "tab_label":            {"en": "Script {n}", "es": "Script {n}", "pt": "Script {n}", "pt_br": "Script {n}", "fr": "Script {n}", "it": "Script {n}", "de": "Skript {n}", "ru": "Скрипт {n}"},

    "about_title":          {"en": "About RLD Manager", "es": "Acerca de RLD Manager", "pt": "Sobre o RLD Manager", "pt_br": "Sobre o RLD Manager", "fr": "À propos de RLD Manager", "it": "Informazioni su RLD Manager", "de": "Über RLD Manager", "ru": "О программе RLD Manager"},
    "about_version":        {"en": "Version 2.0", "es": "Versión 2.0", "pt": "Versão 2.0", "pt_br": "Versão 2.0", "fr": "Version 2.0", "it": "Versione 2.0", "de": "Version 2.0", "ru": "Версия 2.0"},
    "about_description":    {"en": "Multi-file editor for ExHIBIT RLD script files.\nSupports text extraction, reinsertion, XOR encryption,\nbrute-force key search and GYU image decoding.",
                             "es": "Editor multi-archivo para scripts RLD de ExHIBIT.\nSoporta extracción de texto, reinserción, cifrado XOR,\nbúsqueda de claves por fuerza bruta y decodificación de imágenes GYU.",
                             "pt": "Editor multi-ficheiro para scripts RLD do ExHIBIT.\nSuporta extracção de texto, reinserção, cifra XOR,\npesquisa de chaves por força bruta e descodificação de imagens GYU.",
                             "pt_br": "Editor multi-arquivo para scripts RLD do ExHIBIT.\nSuporta extração de texto, reinserção, cifra XOR,\nbusca de chaves por força bruta e decodificação de imagens GYU.",
                             "fr": "Éditeur multi-fichiers pour les scripts RLD d'ExHIBIT.\nSupporte l'extraction de texte, la réinsertion, le chiffrement XOR,\nla recherche de clé par force brute et le décodage d'images GYU.",
                             "it": "Editor multi-file per script RLD di ExHIBIT.\nSupporta estrazione testo, reinserimento, cifratura XOR,\nricerca chiave brute-force e decodifica immagini GYU.",
                             "de": "Mehrdatei-Editor für ExHIBIT RLD-Skriptdateien.\nUnterstützt Textextraktion, Wiedereinfügung, XOR-Verschlüsselung,\nBrute-Force-Schlüsselsuche und GYU-Bilddecodierung.",
                             "ru": "Многофайловый редактор скриптов RLD для ExHIBIT.\nПоддерживает извлечение текста, вставку, шифрование XOR,\nперебор ключей и декодирование изображений GYU."},
    "about_credits":        {"en": "Credits", "es": "Créditos", "pt": "Créditos", "pt_br": "Créditos", "fr": "Crédits", "it": "Crediti", "de": "Danksagungen", "ru": "Авторы"},
    "about_credits_text":   {"en": "Original C# RLD engine:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nGYU image decoder (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  MIT License -- Copyright (C) 2015-2020 by morkt\n\nPython port & app:\n  Dr.Simp\n\nUI framework: PyQt6 + PyQt-Fluent-Widgets\nBuilt with Python 3.11+",
                             "es": "Motor RLD original en C#:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nDecodificador de imágenes GYU (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  Licencia MIT -- Copyright (C) 2015-2020 by morkt\n\nPuerto Python y aplicación:\n  Dr.Simp\n\nFramework UI: PyQt6 + PyQt-Fluent-Widgets\nDesarrollado con Python 3.11+",
                             "pt": "Motor RLD original em C#:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nDescodificador de imagens GYU (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  Licença MIT -- Copyright (C) 2015-2020 by morkt\n\nPorte Python e aplicação:\n  Dr.Simp\n\nFramework UI: PyQt6 + PyQt-Fluent-Widgets\nDesenvolvido com Python 3.11+",
                             "pt_br": "Motor RLD original em C#:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nDecodificador de imagens GYU (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  Licença MIT -- Copyright (C) 2015-2020 by morkt\n\nPorte Python e aplicação:\n  Dr.Simp\n\nFramework UI: PyQt6 + PyQt-Fluent-Widgets\nDesenvolvido com Python 3.11+",
                             "fr": "Moteur RLD original en C# :\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nDécodeur d'images GYU (ImageGYU.cs) :\n  morkt  (github.com/morkt/GARbro)\n  Licence MIT -- Copyright (C) 2015-2020 by morkt\n\nPortage Python et application :\n  Dr.Simp\n\nFramework UI : PyQt6 + PyQt-Fluent-Widgets\nDéveloppé avec Python 3.11+",
                             "it": "Motore RLD originale in C#:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nDecoder immagini GYU (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  Licenza MIT -- Copyright (C) 2015-2020 by morkt\n\nPorting Python e applicazione:\n  Dr.Simp\n\nFramework UI: PyQt6 + PyQt-Fluent-Widgets\nSviluppato con Python 3.11+",
                             "de": "Originaler C#-RLD-Motor:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nGYU-Bilddecoder (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  MIT-Lizenz -- Copyright (C) 2015-2020 by morkt\n\nPython-Port und Anwendung:\n  Dr.Simp\n\nUI-Framework: PyQt6 + PyQt-Fluent-Widgets\nEntwickelt mit Python 3.11+",
                             "ru": "Оригинальный движок RLD на C#:\n  marcussacana  (github.com/marcussacana/RLDManager)\n\nДекодер изображений GYU (ImageGYU.cs):\n  morkt  (github.com/morkt/GARbro)\n  Лицензия MIT -- Copyright (C) 2015-2020 by morkt\n\nПорт на Python и приложение:\n  Dr.Simp\n\nUI-фреймворк: PyQt6 + PyQt-Fluent-Widgets\nРазработано на Python 3.11+"},
    "about_close":          {"en": "Close", "es": "Cerrar", "pt": "Fechar", "pt_br": "Fechar", "fr": "Fermer", "it": "Chiudi", "de": "Schließen", "ru": "Закрыть"},
}


def detect_lang() -> Lang:
    try:
        loc = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
        low = loc.lower().replace("-", "_")
        if low.startswith("pt_br"):
            return "pt_br"
        if low.startswith("pt"):
            return "pt"
        if low.startswith("es"):
            return "es"
        if low.startswith("fr"):
            return "fr"
        if low.startswith("it"):
            return "it"
        if low.startswith("de"):
            return "de"
        if low.startswith("ru"):
            return "ru"
    except Exception:
        pass
    return "en"


class Translator:
    def __init__(self, lang: Optional[Lang] = None):
        self.lang: Lang = lang or detect_lang()

    def set_lang(self, lang: Lang):
        self.lang = lang

    def t(self, key: str, **kwargs) -> str:
        entry = _STRINGS.get(key)
        if entry is None:
            return key
        text = entry.get(self.lang) or entry.get("en") or key
        if kwargs:
            text = text.format(**kwargs)
        return text


_tr = Translator()


def set_lang(lang: Lang):
    _tr.set_lang(lang)


def t(key: str, **kwargs) -> str:
    return _tr.t(key, **kwargs)


def current_lang() -> Lang:
    return _tr.lang
