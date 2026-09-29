# BeScared

> [!CAUTION]
> **Dieses Repository enthält Windows-Skripte, die den normalen Betrieb eines
> Computers stören können. Starte sie nicht auf deinem regulären Computer.**
> Die Skripte können den Bildschirm blockieren, laute Audiodateien abspielen,
> beim Anmelden erneut starten und Windows herunterfahren.

## Sicherheitsbewertung

Behandle den Inhalt als **nicht vertrauenswürdig und potenziell destruktiv**.
Ein erfolgreicher Programmstart ist kein Nachweis dafür, dass das System oder
deine Daten geschützt sind. Auch eine virtuelle Maschine ist nur dann eine
sinnvolle Testumgebung, wenn sie isoliert ist und keine gemeinsamen Ordner,
Anmeldedaten, Zwischenablage oder wichtigen Netzwerkzugänge freigibt.

Führe die Dateien nicht auf fremden Geräten, Arbeits- oder Schulcomputern oder
Systemen mit wichtigen Daten aus. Verwende das Projekt nicht, um andere
Personen zu erschrecken, zu täuschen, zu belästigen oder deren Geräte zu
beeinträchtigen.

## Was der Code erkennen lässt

Die folgenden Punkte stammen aus einer statischen Durchsicht der Skripte. Das
tatsächliche Verhalten hängt unter anderem von Windows, installierten
Programmen und vorhandenen Dateien ab.

- `starte_bescared.py` startet `autostart.ps1` und anschließend
  `bloody-scammer.ps1`. Es übergibt dabei `-WindowCount 9999`, nicht den im bisherigen README behaupteten Wert eins.
- `autostart.ps1` legt im Autostart-Ordner des aktuellen Windows-Benutzers eine
  Verknüpfung an, die `Russk.py` bei späteren Anmeldungen verborgen starten soll.
- `bloody-scammer.ps1` kann sehr viele Fenster öffnen, Audiodateien wiederholt
  abspielen und Fenster im Vordergrund halten. Es startet außerdem weitere Python-Skripte und löst nach etwa 60 Sekunden einen sofortigen Herunterfahrbefehl aus.
- `bloody-scammer.ps1` und `new.py` fragen Informationen zur öffentlichen
  IP-Adresse und zum ungefähren Standort bei `ip-api.com` ab. Die Anfrage verwendet HTTP und ist daher nicht verschlüsselt.
- Die Skripte können Ressourcen stark beanspruchen und die Bedienung des
  Systems erschweren. Ungespeicherte Arbeit kann verloren gehen.

## Archivhinweis

`entpacke_zip.py` erwartet eine Datei namens `42.zip`. Im Repository liegt
jedoch `43.zip`, und `starte_bescared.py` ruft `entpacke_zip.py` nicht auf.
Die bisherige Beschreibung des Startablaufs war daher nicht korrekt.

## Sicherer Umgang

Wenn du den Code untersuchen musst, lies die Skripte zunächst als Text und
führe sie nicht aus. Für eine notwendige dynamische Analyse sollte eine
wegwerfbare, vollständig isolierte virtuelle Maschine ohne persönliche Daten,
gemeinsame Ordner oder Netzwerkverbindung verwendet werden. Sichere wichtige
Daten unabhängig davon regelmäßig.

Diese README ist keine Sicherheitsgarantie und ersetzt weder eine Prüfung des
gesamten Quellcodes noch eine fachkundige Analyse. Änderungen an den Skripten
können die hier beschriebenen Risiken jederzeit verändern.
