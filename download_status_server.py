"""Local, read-only progress page for the FlyWire dataset downloads."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RECORDS = (
    ("FAFB v783 – Verbindungen und Synapsen", DATA / "flywire_fafb_v783", "https://zenodo.org/records/10676866"),
    ("FAFB v783 – 3D-Skelette und Ähnlichkeitsdaten", DATA / "flywire_morphology_v783", "https://zenodo.org/records/10877326"),
)
CODEX_FILE = DATA / "codex_fafb_v783" / "connections_princeton.csv.gz"
CODEX_SIZE = 68_456_801
PIPELINE_STATE = ROOT / "logs" / "pipeline_state.json"
EXTRA_RECORDS = (
    ("Princeton 2025 – neuer Synapsendetektor am selben Gehirn", DATA / "codex_fafb_v783",
     "https://codex.flywire.ai/api/download?dataset=fafb", "princeton_provenance.json", (
         ("connections_princeton_no_threshold.csv.gz", 275_679_780),
         ("fafb_v783_princeton_synapse_table.csv.gz", 2_695_106_039),
     )),
    ("BANC v888 – Gehirn und Bauchmark eines anderen weiblichen Tieres",
     DATA / "research_sources" / "other" / "banc_2026", "https://doi.org/10.7910/DVN/7WTH1N",
     "provenance.json", (
         ("supplemental_data_2.txt", 31_660_830),
         ("banc_888_edgelist_simple_v2.feather", 305_250_378),
         ("banc_888_edgelist_simple_v3.feather", 359_161_658),
     )),
    ("MaleCNS v1.0 – Gehirn und Bauchmark eines männlichen Tieres",
     DATA / "malecns_v1_reference", "https://male-cns.janelia.org/download/", "provenance.json", (
         ("body-annotations-male-cns-v1.0-minconf-0.5.feather", 14_483_314),
         ("body-neurotransmitters-male-cns-v1.0.feather", 43_282_834),
         ("connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather", 508_025_642),
     )),
)
HTML = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fliegen-Daten · Live-Fortschritt</title>
<style>
  :root{color-scheme:dark;font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#0b111a;color:#ebf2fc}
  body{max-width:1000px;margin:auto;padding:30px 22px 80px}
  h1{font-size:2rem;margin:0 0 8px}p{color:#afc0d3;line-height:1.5}
  a{color:#8ad8ff}.top{display:flex;justify-content:space-between;gap:16px;align-items:center}
  .badge{background:#153d4a;border:1px solid #2c7882;padding:7px 12px;border-radius:99px;color:#a8f2e8;font-size:.85rem}
  .card{background:#132031;border:1px solid #2b4055;border-radius:16px;padding:20px;margin:18px 0}
  .file{display:grid;grid-template-columns:1fr auto;gap:4px 16px;padding:12px 0;border-top:1px solid #273a4d}
  .name{font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere;font-size:.88rem}
  .muted{color:#8ea5ba;font-size:.85rem}.value{font-variant-numeric:tabular-nums}
  .bar{height:8px;background:#26394b;border-radius:99px;overflow:hidden;grid-column:1/-1;margin-top:4px}
  .fill{height:100%;background:linear-gradient(90deg,#4a9cdd,#62e2bc);border-radius:99px;transition:width .5s}
  .done{color:#79e1bb}.pending{color:#9ab0c5}.error{color:#ffc18c}
</style></head><body>
<div class="top"><div><h1>Fliegen-Daten · Download</h1><p>FlyWire v783 und ergänzende Nervensystemdaten, ohne Mikroskopbilder. Fertige Archive werden gegen ihre offiziellen Prüfsummen geprüft.</p></div><div class="badge" id="live">● Live</div></div>
<section class="card"><strong>Gesamtfortschritt</strong><div id="summary" class="muted">Wird geladen …</div><div class="bar"><div class="fill" id="totalbar" style="width:0%"></div></div></section>
<section class="card"><strong>Arbeitslauf</strong><div id="pipeline" class="muted">Wird geladen …</div><p class="muted"><a href="http://127.0.0.1:4173/analysis/report.md" target="_blank">Aktuellen Analysebericht öffnen ↗</a></p></section>
<div id="records"></div>
<div id="additional"></div>
<section class="card"><strong>Zelltypen und Annotationen</strong><div id="annotation" class="muted">Wird geladen …</div><p class="muted">Version 2.1.0, passend zur FlyWire-Veröffentlichung von 2024.</p></section>
<p class="muted">Diese Anzeige liest nur den lokalen Downloadstatus. Ein vollständiger Datensatz ist erst nach Prüfsummenvergleich fertig.</p>
<script>
const fmt=x=>x>=1e9?(x/1e9).toFixed(2)+' GB':x>=1e6?(x/1e6).toFixed(1)+' MB':(x/1e3).toFixed(0)+' kB';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function update(){try{
 const r=await fetch('/api/status',{cache:'no-store'}); if(!r.ok)throw Error('HTTP '+r.status); const d=await r.json();
 document.getElementById('summary').textContent=fmt(d.bytes_done)+' von '+fmt(d.bytes_total)+' · '+(100*d.bytes_done/d.bytes_total).toFixed(1)+' %';
 document.getElementById('totalbar').style.width=(100*d.bytes_done/d.bytes_total).toFixed(2)+'%';
 const stageNames={download:'Download läuft',retry:'Erneuter Downloadversuch',analysis:'Gesamtanalyse läuft',complete:'Download und Analyse abgeschlossen',error:'Download benötigt Aufmerksamkeit',analysis_error:'Analyse benötigt Aufmerksamkeit'};
 document.getElementById('pipeline').textContent=(stageNames[d.pipeline?.stage]||'Status noch nicht verfügbar')+(d.pipeline?.stage==='download'&&d.active_file?' · '+d.active_file:'');
 document.getElementById('records').innerHTML=d.records.map(g=>`<section class="card"><h2>${esc(g.name)}</h2><p><a href="${esc(g.url)}" target="_blank">Offizielles Archiv öffnen ↗</a></p>${g.files.map(f=>`<div class="file"><span class="name">${esc(f.name)}</span><span class="value ${f.state==='geprüft'?'done':f.state==='ausstehend'?'pending':''}">${esc(f.state)} · ${fmt(f.done)} / ${fmt(f.size)}</span><div class="bar"><div class="fill" style="width:${(100*f.done/f.size).toFixed(2)}%"></div></div></div>`).join('')}</section>`).join('');
 document.getElementById('additional').innerHTML='<h2>Weitere Forschungsdaten</h2>'+d.additional.map(g=>`<section class="card"><h2>${esc(g.name)}</h2><p><a href="${esc(g.url)}" target="_blank">Quelle öffnen ↗</a></p>${g.files.map(f=>`<div class="file"><span class="name">${esc(f.name)}</span><span class="value ${f.state==='geprüft'?'done':f.state==='ausstehend'?'pending':''}">${esc(f.state)} · ${fmt(f.done)} / ${fmt(f.size)}</span><div class="bar"><div class="fill" style="width:${(100*f.done/f.size).toFixed(2)}%"></div></div></div>`).join('')}</section>`).join('');
 document.getElementById('annotation').textContent=d.annotation.exists?'Vorhanden · '+fmt(d.annotation.size):'Noch nicht abgeschlossen';
 document.getElementById('live').textContent='● Live · '+new Date().toLocaleTimeString('de-DE');
}catch(e){document.getElementById('live').textContent='Verbindung unterbrochen';}}
update();setInterval(update,3000);
</script></body></html>"""


def additional_status() -> list[dict]:
    result = []
    for name, directory, url, manifest_name, entries in EXTRA_RECORDS:
        manifest_path = directory / manifest_name
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            verified = {
                item["path"].replace("\\", "/"): item
                for item in manifest.get("files", []) if "path" in item
            }
        except (OSError, ValueError):
            verified = {}
        files = []
        for filename, size in entries:
            path = directory / filename
            partial = directory / (filename + ".part")
            if not partial.exists():
                partial = directory / (filename + ".partial")
            local_key = str(path.relative_to(ROOT)).replace("\\", "/")
            check = verified.get(local_key)
            if path.is_file() and path.stat().st_size == size:
                matched = check and check.get("bytes") == size and (
                    check.get("md5_base64") == check.get("official_md5_base64") or
                    check.get("md5") == check.get("published_md5")
                )
                done, state = size, "geprüft" if matched else "vorhanden"
            elif partial.exists():
                done, state = min(size, partial.stat().st_size), "lädt"
            else:
                done, state = 0, "ausstehend"
            files.append({"name": filename, "size": size, "done": done, "state": state})
        result.append({"name": name, "url": url, "files": files})
    return result


def status() -> dict:
    records = []
    total = 0
    done_total = 0
    active_file = None
    active_mtime = 0.0
    for name, directory, url in RECORDS:
        metadata_path = directory / "zenodo_record.json"
        if not metadata_path.exists():
            records.append({"name": name, "url": url, "files": []})
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        files = []
        for entry in metadata["files"]:
            size = entry["size"]
            path = directory / entry["key"]
            state_path = path.with_name(path.name + ".progress.json")
            if path.exists() and path.stat().st_size == size:
                done, state = size, "geprüft"
            elif state_path.exists():
                progress = json.loads(state_path.read_text(encoding="utf-8"))
                done = min(size, len(progress.get("completed", [])) * progress["chunk_size"])
                state = "lädt"
                if state_path.stat().st_mtime > active_mtime:
                    active_file, active_mtime = entry["key"], state_path.stat().st_mtime
            else:
                done, state = 0, "ausstehend"
            total += size
            done_total += done
            files.append({"name": entry["key"], "size": size, "done": done, "state": state})
        records.append({"name": name, "url": url, "files": files})
    codex_done = min(CODEX_SIZE, CODEX_FILE.stat().st_size) if CODEX_FILE.exists() else 0
    total += CODEX_SIZE
    done_total += codex_done
    records.insert(0, {
        "name": "Codex v783 – kompakte Arbeitskopie für das 3D-Modell",
        "url": "https://codex.flywire.ai/",
        "files": [{
            "name": "connections_princeton.csv.gz", "size": CODEX_SIZE, "done": codex_done,
            "state": "vorhanden" if codex_done == CODEX_SIZE else "lädt" if codex_done else "ausstehend",
        }],
    })
    for record in records:
        for file in record["files"]:
            if file["state"] == "lädt" and file["name"] != active_file:
                file["state"] = "teilweise"
    annotation = DATA / "flywire_annotations_v2.1.0" / "Supplemental_file1_neuron_annotations.tsv"
    try:
        pipeline = json.loads(PIPELINE_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pipeline = None
    return {
        "records": records,
        "additional": additional_status(),
        "bytes_total": total or 1,
        "bytes_done": done_total,
        "annotation": {"exists": annotation.exists() and annotation.stat().st_size == 27_015_208, "size": annotation.stat().st_size if annotation.exists() else 0},
        "pipeline": pipeline,
        "active_file": active_file,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/api/status":
            body = json.dumps(status(), ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif self.path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("FlyWire download status: http://127.0.0.1:8765/", flush=True)
    server.serve_forever()
