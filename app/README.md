# Fliege im Raum — 3D-Demonstrator

Ein lokal laufender Browser-Prototyp: Eine gegliederte Fruchtfliege bewegt sich ohne vorgegebenes Ziel in einer einfachen 3D-Arena. Die Standardsteuerung ist jetzt ein **abstraktes Eigenaktivitätsmodell** (`autonomy.mjs`) mit vier interagierenden Aktivitätspopulationen (Laufen, links/rechts wenden, Putzen), fortlaufenden internen Schwankungen, langsamen Zuständen (Aktivierung, Ermüdung, Putztrieb) und Wandreizen aus körperrelativen Blickrichtungen. Die Ausgänge bewegen den Körper; seine neue Position liefert im nächsten Schritt die Reize. Dieses Modell wurde nicht an Fliegendaten angepasst. Der Körper besitzt jetzt sechs Beine mit jeweils Coxa, Femur, Tibia und Tarsus, gleitfreie Standfüße, weiche Schwungphasen und Gelenkrückmeldung. Geometrie, Schrittdynamik und Körperproportionen sind eigene Modellannahmen. [Körpermodell, Schnittstelle und Grenzen](./BODY_MODEL.md) beschreiben den aktuellen Stand; eine validierte physikalische oder biologische Simulation steht noch aus.

## Start

Node.js 18 oder neuer genügt; ein Paketmanager ist nicht nötig.

```powershell
node app/server.mjs
```

Dann [Arena](http://127.0.0.1:4173) oder [3D-Neuron-Ankerpunkte](http://127.0.0.1:4173/brain.html) öffnen. Die Seiten brauchen für die lokalen Daten keine Internetverbindung. In beiden 3D-Ansichten lässt sich die Kamera durch Ziehen drehen und mit dem Mausrad zoomen. „Pausieren“ hält die Arena-Bewegung an; „Neustart“ setzt Position **und** interne Zustände zurück. Im ausgeklappten Kasten „Modellinterne Zustände“ kann man beobachten, wie Aktivierung, Ermüdung, Putztrieb und Wandreiz sich während der Bewegung ändern. Der Nutzer gibt der Fliege kein Ziel vor; das Modell enthält dennoch angenommene Dynamik- und Sensorparameter.

Der Forschungsprototyp greift die Idee spontaner Bewegungsvariabilität und interner Kontrolle aus [Gattuso et al., PNAS 2025](https://doi.org/10.1073/pnas.2407626122) auf. Die Rückkopplung zwischen Körper, Sensoren und Umgebung ist eine stark vereinfachte Analogie zu [NeuroMechFly v2 / FlyGym](https://doi.org/10.1038/s41592-024-02497-y). Seine Gleichungen und Parameter sind **eigene, unkalibrierte Hypothesen**; aus beiden Arbeiten wurde kein fertiges Modell übernommen.

Die separate Punktansicht zeigt zunächst 21.310 tatsächlich annotierte `pos_x/y/z`-Anker aus 139.255 Zeilen der gepinnten FlyWire-Annotation v2.1.0. Die schnelle Exportdatei `data/brain-anchor-points.json` ist 1,0 MB groß. „Alle Anker laden“ ruft erst auf Wunsch die vollständige lokale Punktdatei `data/brain-anchor-points-all.json` (6,6 MB) ab; deren Darstellung kann auf schwächeren Geräten langsamer sein. Der reproduzierbare Stichprobenexport nimmt alle Klassen mit höchstens 2.500 Einträgen vollständig und jeweils ungefähr ein Achtel der größeren `super_class`-Gruppen anhand eines stabilen Root-ID-Hashes. Beide Dateien rechnen die Quellvoxel (4 × 4 × 40 nm) in µm um und bewahren Root-IDs als exakte Strings. Neu erstellen: `node app/export_anchor_points.mjs`. Die Punkte sind **Anker**, keine vollständige Hirnform und keine Neuronen-Skelette; letztere gehören zum separaten Morphologiearchiv [Zenodo 10877326](https://zenodo.org/records/10877326). `pos_*` ist außerdem nicht mit den nur teilweise vorhandenen `soma_*`-Koordinaten gleichzusetzen.

Die Datenanzeige ruft über den lokalen App-Server den Downloadstatus auf Port 8765 ab. Sie zeigt den Fortschritt der FlyWire-Dateien und prüft, ob `brain/graph-original-v783` samt `brain-csr-v1`-Manifest und den erwarteten Dateigrößen vorliegt. Dieser Graph stammt aus der freigegebenen `proofread_connections_783.feather` und enthält 139.255 Root-IDs, 15.091.983 gerichtete Neuronenpaare und 54.492.922 Synapsen zwischen beidseitig proofread Partnern. Die rund 213 MB binären Grapharrays werden im Browser-Worker geladen, während `annotations.json` nur für den kleinen Kandidatenauszug auf dem App-Server gelesen wird. „Live-Download ansehen“ öffnet die ausführliche lokale Fortschrittsseite. „Vorläufigen Teilbericht öffnen“ liefert ausschließlich die vorhandene Datei `analysis/report.md`; sie kann während der laufenden Analyse aktualisiert werden. Ein vorhandener Graph schaltet die Graphsteuerung allein **nicht** frei.

## Umschaltung und Worker-Schnittstelle

„Eigenaktivität“ verwendet `autonomy.mjs`; die ältere Demo-Heuristik in `control.mjs` bleibt als Referenz erhalten und steuert die Arena nicht mehr. Sobald `brain/graph-original-v783` vollständig vorhanden ist, startet die Seite automatisch den **echten** Modul-Worker `brain/worker.mjs`. Der App-Server stellt dafür `/brain/worker.mjs`, `/brain/engine.mjs`, `/brain/web.mjs` und die erlaubten Graphdateien bereit. `brain-bridge.mjs` sendet `{type:'load', baseUrl:'/brain/graph-original-v783'}` und prüft die Antwort `{type:'loaded', manifest}` gegen den lokalen Graphstatus. Das `dataset` und die Neuronen- und Kantenzahlen müssen zwischen Server und Worker übereinstimmen.

„Graph-Inspektion“ wird nach dem Laden freigeschaltet. Dort ruht die Fliege: Die Oberfläche zeigt Neuronen- und Kantenzahlen aus dem tatsächlich geladenen Originalmanifest sowie DNa02- und DNg13-Kandidaten mit exakten Root-ID-Strings aus `annotations.json` (FlyWire-Annotationen v2.1.0). Diese Zellnamen belegen keine Steuerfunktion für den vereinfachten Körper. Der Worker lädt **ohne MotorMap** und liefert daher keine `controlFrame`-Werte. „FlyWire-Steuerung“ bleibt deaktiviert. Das separate, kleinere `brain/graph-v783` aus dem vorgefilterten Codex-Export ist für die Inspektion nicht mehr die Standardquelle.

Für eine künftige experimentelle Steuerung müssen **beide Seiten** der Schleife explizit definiert sein: eine `fly.motor-map.v1`-Zuordnung und ein `fly.sensor-adapter.v1`. Beide verlangen exakte Root-ID-Strings, eine HTTPS-Quellen-URL und eine Hypothesenbegründung pro Kanal. Ihre `dataset`-Angabe muss exakt zum Graph-Manifest passen. `window.FlyDemo.setMotorMap(spec)` validiert die Motorzuordnung und lädt den Worker mit dessen `motorMap` neu. Beispiel mit Platzhaltern, die vor Verwendung durch belegte Werte ersetzt werden müssen:

```js
window.FlyDemo.setMotorMap({
  schema: 'fly.motor-map.v1',
  dataset: window.FlyDemo.getStatus().workerGraph.dataset,
  channels: {
    forward: {
      rootIds: ['<exakte dezimale Root-ID>'],
      evidenceUrl: 'https://<Fachquelle-zur-Zellfunktion>',
      hypothesis: 'Begründete Hypothese, warum dieser Zelltyp hier Vorwärtsbewegung abbildet.',
    },
  },
});
```

Mögliche Motorkanäle sind `forward`, `turnLeft`, `turnRight`, `wing` und `groom`. Der Sensoradapter übersetzt eine Beobachtung der Arena in Eingänge an **nur die deklarierten** Neuronen. Die folgende Vorlage verwendet Wandnähe als *hypothetische* Größe; ein passender sensorischer Root-ID-Typ und seine Quellenangabe fehlen derzeit und müssen vor Verwendung recherchiert werden:

```js
const sensoryRootId = '<exakte dezimale Root-ID>';
window.FlyDemo.setSensorAdapter({
  schema: 'fly.sensor-adapter.v1',
  dataset: window.FlyDemo.getStatus().workerGraph.dataset,
  channels: {
    wallProximity: {
      rootIds: [sensoryRootId],
      evidenceUrl: 'https://<Fachquelle-zur-Sensorfunktion>',
      hypothesis: 'Wandnähe wird versuchsweise in einen Eingangsstrom für diese Zelle umgerechnet.',
    },
  },
  encode({ x, z, arenaRadius }) {
    const nearness = Math.max(0, 1 - (arenaRadius - Math.hypot(x, z)));
    return { stimuli: { [sensoryRootId]: nearness }, forceSpikes: [] };
  },
});
```

`encode()` darf nur deklarierte Root-IDs und endliche Ströme zwischen −10 und +10 (arbiträre Modelleinheiten) ausgeben. Ein Quellenlink und ein Erklärungstext dokumentieren die Herkunft; die Anwendung kann ihre wissenschaftliche Aussagekraft nicht selbst überprüfen. **Derzeit sind weder eine Sensorzuordnung noch eine MotorMap hinterlegt.** Deshalb bleibt „FlyWire-Steuerung“ gesperrt. DNa02/DNg13 sind Forschungs-Kandidaten für Laufsteuerung, aber die notwendige Eingangszuordnung und die Übertragung auf diesen 3D-Körper sind nicht geklärt.

Im späteren Graphsteuerungsmodus ruft die Seite `encode()` auf und sendet die resultierenden `stimuli`/`forceSpikes` mit `type:'step'` an den Worker. Nur dessen `state.controlFrame` wird in `fly.control.v1`-Bewegung umgesetzt. Der Frame verfällt nach 350 ms; ohne Signal ruht die Fliege. `window.FlyDemo.getObservation()` liefert Position, Richtung, Arenaradius, den zusätzlichen `body`-Zustand und einen Zeitstempel (`performance.timeOrigin + performance.now()`). `getStatus()` liefert auch einen Auszug der modellinternen Eigenaktivitätszustände. `selectAutonomy()` (bisheriger Alias `selectDemo()`), `selectInspect()`, `selectBrain()`, `clearMotorMap()`, `clearSensorAdapter()` und `retryAutomaticWorker()` sind weitere Integrationspunkte. Der Graph enthält keine validierte Körpersteuerung und keine vollständige sensorisch-motorische Schleife.

Als nächster Forschungsschritt müssen sensorische Root-IDs für eine klar definierte Arenagröße, DNa02/DNg13-Ausgangsrollen, Stromskala, Zeitverzögerung und die Umrechnung neuronaler Aktivität in Drehung bzw. Schrittfolge mit Primärquellen und Perturbationstests belegt werden. [Fine-grained descending control of steering in walking Drosophila](https://doi.org/10.1016/j.cell.2024.08.033) stützt die Beteiligung von DNa02 und DNg13 an unterschiedlichen Lauf-Wendegesten; daraus folgt noch keine eindeutige Zuordnung zu den vier Kanälen dieses Demonstrators.

## Test

```powershell
node --test app/tests/*.test.mjs
```

Die Tests prüfen Frame-Validierung, Worker-Handshake, Rückfall bei ausbleibenden Daten und reproduzierbare sowie begrenzte Eigenaktivität. Ein längerer geschlossener Arenadurchlauf prüft, dass Laufen, Wenden, Ruhen und Putzen ohne Zielvorgabe auftreten und die Fliege nicht dauerhaft am Rand hängt.

## Dateien und Lizenz

- `index.html`, `style.css`, `main.js`: Browseransicht, Nahkamera und Körperintegration.
- `body-kinematics.mjs`, `articulated-fly.mjs`: Gelenkgeometrie, Fußkontakte, Gangkoordination und prozeduraler Fliegenkörper.
- `BODY_MODEL.md`: Koordinaten, Körperbeobachtungsschnittstelle, Quellen und Modellgrenzen.
- `autonomy.mjs`: eigenständiges, hypothetisches Aktivitätsmodell mit Körper-Rückkopplung; keine FlyWire-Neuronenidentität.
- `brain.html`, `brain.css`, `brain.js`: drehbare Ansicht gemessener räumlicher Ankerpunkte.
- `export_anchor_points.mjs`, `data/brain-anchor-points*.json`: reproduzierbare Stichprobe und optionaler Vollauszug aus der gepinnten Annotation.
- `control.mjs`: ältere Demo-Heuristik und externe Frame-Schnittstelle.
- `brain-bridge.mjs`: Protokoll für den vorhandenen `brain/worker.mjs`, einschließlich `load`, `step` und `state`.
- `motor-map.mjs`, `sensor-map.mjs`: prüfen die expliziten Hypothesen für Motorik und Sensorik vor Freischaltung.
- `status.mjs`, `server.mjs`: Graphprüfung, lokaler Datenstatus-Proxy und Dateiserver.
- `vendor/three.module.js`, `vendor/three.core.js`: Three.js r186 (MIT); Lizenz in `vendor/THREE-LICENSE.txt`.
