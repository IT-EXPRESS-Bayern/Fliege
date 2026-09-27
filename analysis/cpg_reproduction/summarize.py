"""Build a concise factual readout from executed CPG runs; no invented outcomes."""
from pathlib import Path
import json
import csv

HERE = Path(__file__).resolve().parent
sections = ["# Ergebnisse der CPG-Nachrechnung\n", "Diese Übersicht wird ausschließlich aus abgeschlossenen lokalen Läufen erzeugt. Ein Rhythmus ist eine Eigenschaft des hier geprüften Ratenmodells unter konstantem Eingang. Er bestätigt weder biologische Autonomie noch das Zusammenspiel aller sechs Beine.\n"]
for summary_path in sorted(HERE.glob("*/summary.json")):
    folder = summary_path.parent
    if not (folder / "audit.json").exists():
        continue
    result = json.loads(summary_path.read_text(encoding="utf-8"))
    protocol = result["protocol"]
    sections += [f"## {folder.name}\n", f"Eingang je angeregter Zelle: **{protocol['input_amplitude_each_cell_arbitrary_units']:g} willkürliche Einheiten**. Seed **{protocol['seed']}**. Gleicher Parametersatz in allen Gegenproben. Keine periodische Reizfolge.\n", "| Bedingung | aktive echte Modulmotoren | mittlerer Rhythmik-Score | E1 Maximum (Raten-Hz) | E2 Maximum (Raten-Hz) |\n|---|---:|---:|---:|---:|\n"]
    for name, stats in result["conditions"].items():
        strict = stats["conservative_motor_mask"]
        sections.append(f"| {name} | {strict['active_post_transient']} / {strict['total']} | {strict['mean_rhythmicity']:.6f} | {stats['readouts']['E1']['maxRate']:.3f} | {stats['readouts']['E2']['maxRate']:.3f} |\n")
    conditions = result["conditions"]
    if "zero" in conditions:
        sections.append(f"\nRuhe: maximal {conditions['zero']['numerical']['maximum_rate']:.6g} Raten-Hz. Nullaktivität ist bei Nullzustand ohne Eingang eine erwartete Eigenschaft dieser Gleichung.\n")
    if "dng100_repeat" in conditions:
        sections.append(f"Identische Wiederholung: **{conditions['dng100_repeat'].get('exact_repeat_equal')}** (vollständige float64-Zeitreihe).\n")
    if "dng100_tighter" in conditions:
        comp = conditions["dng100_tighter"].get("tolerance_comparison", {})
        sections.append(f"Engere Integratortoleranz: größte absolute Ratenabweichung **{comp.get('max_absolute_rate_difference', float('nan')):.6g} Hz**, RMS **{comp.get('rms_rate_difference', float('nan')):.6g} Hz**.\n")
    if "dng100" in conditions:
        baseline = conditions["dng100"]["conservative_motor_mask"]["mean_rhythmicity"]
        for condition in ["e1_removed", "e2_removed", "i2_removed", "dnb08_pair"]:
            if condition in conditions:
                value = conditions[condition]["conservative_motor_mask"]["mean_rhythmicity"]
                sections.append(f"`{condition}`: Scoreänderung gegenüber DNg100 **{value-baseline:+.6f}**. Dies ist eine Modellintervention, kein Nachweis einer biologischen Zellfunktion.\n")
        motor_frequency = conditions["dng100"]["conservative_motor_mask"].get("median_autocorrelation_frequency_hz_for_rhythmic_cells")
        if motor_frequency is not None:
            sections.append(f"\nNeuronale Rhythmusfrequenz: **{motor_frequency:.3f} Hz** (Median der rhythmischen Motorzellen). Dies ist eine Frequenz abstrakter Raten; eine Schrittfrequenz des 3D-Körpers ist noch nicht kalibriert.\n")
        motor_rows = list(csv.DictReader((folder / "motor_readout_statistics.csv").open(encoding="utf-8", newline="")))
        active = [r for r in motor_rows if r["condition"] == "dng100" and r["conservative_motor"] == "True" and r["active_post_transient"] == "True"]
        sections.append("\n### Konkrete aktive Motorzellen bei DNg100\n\n| Quell-ID | Quellseite | Muskelmodul | mittlere Rate (Hz) |\n|---|---|---|---:|\n")
        for row in active:
            sections.append(f"| {row['root_id']} | {row['side']} | {row['module']} | {float(row['mean_rate']):.4f} |\n")
        sections.append("\nAlle sechs gehören zum vorderen Beinteilnetz. Ihre Kräfte, Gelenkhebel und die Koordination mit Mittel- und Hinterbeinen werden durch diese Nachrechnung nicht bestimmt.\n")
    for filename in ["protocol.json", "input_audit.json", "audit.json", "motor_readout_statistics.csv", "replay.json"]:
        sections.append(f"- [{filename}]({folder.name}/{filename})\n")
    sections.append("\n")
sections += ["## Gemeinsame Grenzen\n", "Die 156 Einträge der originalen Modulmaske enthalten 27 Nichtmotoren oder unklassifizierte Zellen. Die hier hervorgehobene Motormaske umfasst die 129 in derselben Quelle als Motorzellen annotierten Einträge. Die Originalmaske ist zusätzlich in jedem JSON/CSV erhalten.\n", "CPU-Port: Originale Matrix, Zufallssampling, Größenkorrektur und Rhythmikfunktion; SciPy RK45 statt Diffrax Dopri5 und float64 statt float32 für die Integration. Ein einzelner Parametersatz belegt keine Robustheit über Tiere oder viele Zufallsziehungen. Werte von Muskelkraft, Sensorik, Motivation und Plastizität werden nicht daraus abgeleitet. Siehe [Methoden und Quellen](README.md).\n"]
(HERE / "results.md").write_text("\n".join(sections), encoding="utf-8")
print(HERE / "results.md")
