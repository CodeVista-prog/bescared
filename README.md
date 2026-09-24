# !!! KRITISCHER SICHERHEITSHINWEIS !!!

## Dieses Projekt kann deinen Computer massiv beeinträchtigen

Dieses Projekt ist **kein harmloses Spielzeug**. Eine Ausführung kann je nach
Skriptversion, Windows-Konfiguration und vorhandenen Dateien unter anderem zu
folgenden Folgen führen:

- unzähligen Fenstern, die den Desktop und die Bedienung blockieren,
- sehr hoher CPU-, RAM- und Audioauslastung,
- einem instabilen oder nicht mehr reagierenden System,
- erzwungenem Abmelden oder Neustart,
- Verlust ungespeicherter Arbeit,
- beschädigten oder überschriebenen Dateien,
- einem vollständig unbrauchbaren Benutzerkonto oder System,
- unerwarteten Zugriffen auf externe Internetdienste,
- dauerhaftem Datenverlust, wenn keine Sicherung vorhanden ist.

Im schlimmsten Fall können wichtige Programme, laufende Prozesse oder Dateien
beeinträchtigt werden. **Es gibt keine Garantie, dass Windows danach normal
weiterläuft.**

## Was gestartet wird

`starte_bescared.py` entpackt zunächst `42.zip` über `entpacke_zip.py` und
startet danach `bloody-scammer.ps1`. Der Python-Starter begrenzt die Anzahl
der angeforderten Fenster auf eins, das PowerShell-Skript kann aber trotzdem
Audio abspielen, Fenster im Vordergrund anzeigen und externe Dienste aufrufen.

## Nur mit ausdrücklicher Erlaubnis

Starte die Dateien ausschließlich auf einem eigenen Testgerät oder in einer
isolierten virtuellen Maschine. Führe sie niemals auf fremden Computern,
Arbeitsgeräten, Schulrechnern oder Geräten mit wichtigen Daten aus.

Vor jeder Ausführung:

1. wichtige Daten vollständig sichern,
2. alle Dateien und Skripte manuell prüfen,
3. Netzwerkzugriff und Audioausgabe berücksichtigen,
4. offene Programme und ungespeicherte Arbeit schließen,
5. sicherstellen, dass eine Wiederherstellung des Systems möglich ist.

## Haftungsausschluss

Die Nutzung erfolgt vollständig auf eigene Gefahr. Der Autor übernimmt keine
Haftung für Datenverlust, beschädigte Dateien, Systemausfälle, Hardware- oder
Softwareschäden, unerwünschte Netzwerkzugriffe oder sonstige direkte und
indirekte Folgen. Dieses Projekt darf nicht dazu verwendet werden, andere
Personen zu belästigen, zu täuschen, zu erschrecken oder deren Computer zu
beeinträchtigen.

## Nicht getestet

Die Dateien wurden nicht automatisch ausgeführt oder getestet. Vor einer
Nutzung muss der vollständige Inhalt aller Skripte geprüft werden.
