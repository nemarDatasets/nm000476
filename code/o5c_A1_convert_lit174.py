"""src-literature-174 (OSF jq6z4, CC-BY-4.0; Hoy et al. 2024 PNAS doi:10.1073/pnas.2322869121, "Beta and theta oscillations track effort
and previous reward in the human basal ganglia and prefrontal cortex during decision making") -> BIDS-iEEG DERIVATIVE.
Source: preprocessed_data/PFC0x_stim_preproc_osr.mat (MAT v5; sbj_data.ts FieldTrip epochs, 2 bipolar channels labelled e.g. STN/FPC,
-2..9 s per trial; sbj_data.bhv per-trial behaviour; sbj_data.mdl) -> acq-preproc epoched files with bhv fields as events.
raw_data/<ID>_neural_data_run<k>.mat: continuous exports (signal 2 x N at Fs=422 Hz, or datar N x 4 at SR=500 Hz for PFC01) -> acq-raw
continuous runs (channel order not documented in the release: names ch1..). Behavioural raw MAT files (with exact session timestamps)
are not copied; their trial tables are not sample-synchronised in the release, so no events are written for the acq-raw runs.
Usage: python o5c_A1_convert_lit174.py <open500 record dir> <bids root>"""
import glob, json, os, re, sys
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o5c_A1_common import write_run, write_epochs, events_json, wtsv, wjson, mat_strings, flag_strings, finalize_common, copy_code, copy_sourcedata, add_electrodes_na

REC, OUT = sys.argv[1], sys.argv[2]
PRE = os.path.join(REC, "files", "preprocessed_data"); RAW = os.path.join(REC, "files", "raw_data")
report = {"recordings": [], "privacy_flags": [], "behavioral_dates_ym": {}}
priv = set()
scans = {}
labels_by_sub = {}
fs_by_sub = {}
SIDE = {"STN": "subthalamic nucleus (DBS lead, bipolar)", "GPi": "globus pallidus internus (DBS lead, bipolar)", "FPC": "frontopolar cortex (prefrontal lead, bipolar)", "OFC": "orbitofrontal cortex (prefrontal lead, bipolar)"}
TYPE = {"STN": "DBS", "GPi": "DBS", "FPC": "ECOG", "OFC": "ECOG"}
# --- preprocessed epochs
for p in sorted(glob.glob(os.path.join(PRE, "*_stim_preproc_osr.mat"))):
    sid = re.match(r"([A-Z]+\d+)_", os.path.basename(p))[1]
    priv |= mat_strings(p)
    m = sio.loadmat(p, squeeze_me=True, struct_as_record=False)["sbj_data"]
    ts = m.ts; bhv = m.bhv
    labels = [str(x) for x in np.atleast_1d(ts.label)]
    fs = float(ts.fsample)
    trials = [np.asarray(t, dtype=np.float64).T for t in np.atleast_1d(ts.trial)]  # (ch, samples) -> (samples, ch)
    times = [np.asarray(t, dtype=float).ravel() for t in np.atleast_1d(ts.time)]
    n = len(trials)
    keys = [k for k in bhv._fieldnames if np.asarray(getattr(bhv, k)).size == n]
    other = {k: np.asarray(getattr(bhv, k)).ravel().tolist() for k in bhv._fieldnames if k not in keys}
    rows = []
    for k in range(n):
        row = []
        for kk in keys:
            v = np.asarray(getattr(bhv, kk)).ravel()[k]
            v = float(v)
            row.append("n/a" if not np.isfinite(v) else (int(v) if v == int(v) else round(v, 6)))
        rows.append(row)
    sub = f"sub-{sid}"; D = os.path.join(OUT, sub, "ieeg"); stem = f"{sub}_task-effort_acq-preproc"
    r = write_epochs(D, stem, trials, fs, labels, ["n/a"] * len(labels), [TYPE.get(l, "SEEG") for l in labels], {
        "TaskName": "effort",
        "TaskDescription": "Effort-based decision-making (apple-gathering task, 'AGT for core protocol 2018'): on each trial an offer of a reward (stake, apples) for a grip-force effort level (fraction of maximum voluntary contraction) was shown and the patient accepted or rejected it, then squeezed if accepted. Recorded intraoperatively during DBS surgery. Preprocessed trials (-2 to 9 s) with the authors' per-trial behavioural table (sbj_data.bhv) and model-derived values (SV, p_accept, ...).",
        "Instructions": "n/a (see article)",
        "PowerLineFrequency": 60,
        "SoftwareFilters": {"AuthorsPreprocessing": {"Description": "Release file *_stim_preproc_osr.mat: preprocessed, epoched FieldTrip data (sbj_data.ts); steps as described in the article. Values written unchanged."}},
        "HardwareFilters": "n/a",
        "iEEGReference": "bipolar (two re-referenced channels per subject, labels from the release: %s)" % ", ".join(labels),
        "iEEGPlacementScheme": "one basal-ganglia DBS lead (STN or GPi) and one prefrontal electrode (FPC or OFC) per subject (article); no coordinates in the release",
        "ElectricalStimulation": False, "Manufacturer": "n/a",
    }, keys, rows, ch_extra=[{"description": SIDE.get(l, l), "group": l} for l in labels],
        comment=f"o5c_A1_convert_lit174.py: {os.path.basename(p)} sbj_data.ts.trial back-to-back, float32", trial_times=times)
    events_json(os.path.join(D, stem + "_events.json"), {k: {"Description": f"sbj_data.bhv.{k} as released (per trial)"} for k in keys})
    wjson(os.path.join(OUT, "code", stem + "_bhvextra.json"), {"Description": "sbj_data.bhv fields that are not per-trial vectors (index lists), and sbj_data.mdl", "bhv_other": other,
                                                       "mdl": {"par": np.asarray(m.mdl.par).ravel().tolist(), "fit": float(np.asarray(m.mdl.fit).ravel()[0])}, "desp": str(m.desp)})
    r.update(sub=sub, stem=stem, file=os.path.basename(p), labels=labels, bhv_keys=keys)
    report["recordings"].append(r); labels_by_sub[sid] = labels; fs_by_sub[sid] = fs
    scans.setdefault(sub, []).append([f"ieeg/{stem}_ieeg.vhdr", "n/a"])
    print(stem, json.dumps({k: v for k, v in r.items() if k not in ("bhv_keys",)}), flush=True)
# --- raw continuous runs (pre-scan the sampling rates stored in the raw files per subject)
raw_fs = {}
for p in sorted(glob.glob(os.path.join(RAW, "*_neural_data_run*.mat"))):
    sid0 = re.match(r"([A-Z]+\d+)_", os.path.basename(p))[1]
    w = dict((n, sh) for n, sh, c in sio.whosmat(p))
    if "Fs" in w or "SR" in w:
        v = sio.loadmat(p, variable_names=["Fs", "SR"])
        raw_fs[sid0] = float(np.asarray(v.get("Fs", v.get("SR"))).ravel()[0])
for p in sorted(glob.glob(os.path.join(RAW, "*_neural_data_run*.mat"))):
    mm = re.match(r"([A-Z]+\d+)_neural_data_run(\d+)\.mat$", os.path.basename(p))
    sid, run = mm[1], int(mm[2])
    priv |= mat_strings(p)
    m = sio.loadmat(p)
    if "datar" in m:
        X = np.asarray(m["datar"], dtype=np.float64); fs = float(np.asarray(m["SR"]).ravel()[0]); var = "datar"; fs_src = "variable SR in the file"
    else:
        X = np.asarray(m["signal"], dtype=np.float64).T; var = "signal"
        if "Fs" in m:
            fs = float(np.asarray(m["Fs"]).ravel()[0]); fs_src = "variable Fs in the file"
        elif sid in raw_fs:
            fs = raw_fs[sid]; fs_src = "no Fs variable in this file; sampling rate taken from the subject's other raw run (variable Fs)"
        else:
            fs = fs_by_sub[sid]; fs_src = "no Fs variable in the file; sampling rate taken from the subject's preprocessed file (sbj_data.ts.fsample)"
    nch = X.shape[1]
    names = [f"ch{i + 1}" for i in range(nch)]
    lab = labels_by_sub.get(sid)
    desc = "continuous export, variable %s column/row %d; the release does not document the channel order%s" % (var, 0, (" (the subject's preprocessed channels are %s)" % "/".join(lab)) if lab else "")
    sub = f"sub-{sid}"; D = os.path.join(OUT, sub, "ieeg"); stem = f"{sub}_task-effort_acq-raw_run-{run}"
    r = write_run(D, stem, X, fs, names, ["n/a"] * nch, ["SEEG"] * nch, {
        "TaskName": "effort",
        "TaskDescription": "Effort-based decision-making task (see acq-preproc files); continuous intraoperative recording of one task run as exported in the release (raw_data/<ID>_neural_data_run<k>.mat). Trial timing for these runs is only available through the behavioural MAT files and sync pulses of the release, which are not sample-synchronised here (no events.tsv).",
        "Instructions": "n/a (see article)", "PowerLineFrequency": 60,
        "SoftwareFilters": "n/a", "HardwareFilters": "n/a", "SamplingFrequencySource": fs_src, "SoftwareFiltersDescription": "export as released; whether the authors filtered it is not stated",
        "iEEGReference": "n/a (not stated in the release; the preprocessed data are bipolar)",
        "iEEGPlacementScheme": "basal-ganglia DBS lead and prefrontal electrode (article); no coordinates in the release",
        "ElectricalStimulation": False, "Manufacturer": "n/a",
    }, ch_extra=[{"description": desc.replace("column/row 0", f"column/row {i + 1}")} for i in range(nch)], comment=f"o5c_A1_convert_lit174.py: {os.path.basename(p)} {var} float64 -> float32")
    r.update(sub=sub, stem=stem, file=os.path.basename(p), variable=var, fs_source=fs_src)
    report["recordings"].append(r)
    scans.setdefault(sub, []).append([f"ieeg/{stem}_ieeg.vhdr", "n/a"])
    print(stem, json.dumps(r), flush=True)
# behavioural file dates (year-month only) for the README; files not copied
for p in sorted(glob.glob(os.path.join(RAW, "*_behavioral_data_run*.mat"))):
    try:
        b = sio.loadmat(p, squeeze_me=True, struct_as_record=False)["result"]
        st = str(np.atleast_1d(b.startTimes)[0])
        report["behavioral_dates_ym"][os.path.basename(p)] = st[:7] + "-01" if re.match(r"\d{4}-\d{2}-\d{2}", st) else "n/a"
    except Exception as e:
        report["behavioral_dates_ym"][os.path.basename(p)] = "err " + repr(e)[:80]
for sub, rows in scans.items():
    wtsv(os.path.join(OUT, sub, f"{sub}_scans.tsv"), ["filename", "acq_time"], sorted(rows))
subs = sorted(scans)
wtsv(os.path.join(OUT, "participants.tsv"), ["participant_id", "age", "sex", "source_id", "channels_preproc"], [[s, "n/a", "n/a", s[4:], "/".join(labels_by_sub.get(s[4:], [])) or "n/a"] for s in subs])
wjson(os.path.join(OUT, "participants.json"), {"age": {"Description": "not in the release"}, "sex": {"Description": "not in the release"}, "source_id": {"Description": "subject code in the release file names (PFC = prefrontal cohort; PMC10 has raw runs only)"}, "channels_preproc": {"Description": "bipolar channel labels of the preprocessed release file (basal ganglia / prefrontal site)"}})
add_electrodes_na(OUT, "No electrode coordinates are released; one basal-ganglia DBS lead (STN or GPi) and one prefrontal electrode (FPC or OFC) per subject (article). x, y, z = n/a.", types=("ECOG", "SEEG", "DBS"), spatial_ref="n/a (no coordinates released)")
report["privacy_flags"] = flag_strings(priv)
SD = os.path.join(OUT, "sourcedata", "osf-jq6z4")
copy_sourcedata([(p, os.path.relpath(p, os.path.join(REC, "files"))) for p in sorted(glob.glob(os.path.join(PRE, "*.mat")) + glob.glob(os.path.join(RAW, "*_neural_data_run*.mat")))], SD, scrub=True)
open(os.path.join(SD, "NOT_COPIED_release_files.txt"), "w").write("raw_data/*_behavioral_data_run*.mat, raw_data/PFC05_stim_behavior/*, raw_data/SqueezeSubjectSyncSummary_anonymized.xlsx: behavioural/sync files with exact session timestamps; not redistributed here (available in the OSF release). Their per-trial behaviour is in the acq-preproc events.tsv (sbj_data.bhv).\n")
copy_code(OUT, [__file__])
Rr = report["recordings"]; hrs = sum(r["duration_s"] for r in Rr) / 3600
finalize_common(OUT,
    name="Hoy2024 effort decision LFP: subthalamic/pallidal and prefrontal recordings during an effort-based decision task (DBS surgery)",
    dtype="derivative", license_="CC-BY-4.0",
    authors=["Colin W. Hoy", "Coralie de Hemptinne", "Sarah S. Wang", "Catherine J. Harmer", "Matthew A. J. Apps", "Masud Husain", "Philip A. Starr", "Simon Little"],
    refs=["https://doi.org/10.1073/pnas.2322869121", "https://doi.org/10.1101/2023.12.05.570285", "https://doi.org/10.17605/OSF.IO/JQ6Z4"],
    howto="Cite Hoy CW, de Hemptinne C, Wang SS, Harmer CJ, Apps MAJ, Husain M, Starr PA, Little S (2024). Beta and theta oscillations track effort and previous reward in the human basal ganglia and prefrontal cortex during decision making. PNAS 121(31):e2322869121, doi:10.1073/pnas.2322869121, and the OSF release doi:10.17605/OSF.IO/JQ6Z4.",
    keywords=["local field potential", "subthalamic nucleus", "globus pallidus", "prefrontal cortex", "effort", "reward", "decision making", "deep brain stimulation", "beta", "theta"],
    source=[{"DOI": "doi:10.17605/OSF.IO/JQ6Z4", "URL": "https://osf.io/jq6z4/", "Version": "OSF node jq6z4 (files as downloaded 2026-10-11; sha256 in sourcedata/osf-jq6z4/DEIDENTIFICATION_MANIFEST.tsv)"}],
    generated_by=[{"Name": "o5c_A1_convert_lit174.py", "Description": "Repackaging of the preprocessed FieldTrip epochs (acq-preproc, with sbj_data.bhv as events) and of the continuous neural exports (acq-raw) into BrainVision float32. Code in code/."}],
    ethics=["Collected under the source study's approval (see the article, doi:10.1073/pnas.2322869121)."],
    funding=["Wellcome Trust 226645/Z/22/Z", "NIH NINDS K23NS120037", "NIH NIMH F32MH132174", "UKRI BBSRC BB/R010668/2"],
    readme=f"""# Hoy et al. 2024: basal ganglia and prefrontal LFP during effort-based decisions (intraoperative DBS recordings)

{len(subs)} subjects, {len(Rr)} recordings, {hrs:.2f} h. Released by the authors on OSF (doi:10.17605/OSF.IO/JQ6Z4, CC-BY-4.0).

## Organisation (DatasetType derivative)
- `*_acq-preproc_ieeg.vhdr` (PFC01, PFC03, PFC04, PFC05): the authors' preprocessed, epoched bipolar signals (`sbj_data.ts`, trials
  -2 to 9 s around the offer, 422 or 500 Hz) with the two channel labels of the release (STN or GPi; FPC or OFC), written
  back-to-back with one `New Segment` marker per trial. `events.tsv` carries every per-trial field of `sbj_data.bhv` (key, rt,
  block, effort, stake, decision, previous-trial values, model values SV/EFFs/p_accept/dec_ease, ...); `code/*_bhvextra.json` holds the
  index lists (good_key_ix, reject_ix, ...) and the model parameters (`sbj_data.mdl`).
- `*_acq-raw_run-<k>_ieeg.vhdr` (all five subjects, two runs each): the continuous neural exports of `raw_data/` (`signal` 2 x N at
  422 Hz, or `datar` N x 4 at 500 Hz for PFC01) written unchanged. The release does not document the channel order or units of these
  exports (channels `ch1..`, `units` n/a) and the behavioural trial timestamps are on a separate clock (sync files), so these runs
  have no events.tsv.
- No electrode coordinates are released (`electrodes.tsv` with n/a). Age and sex are not in the release.
- `sourcedata/osf-jq6z4/`: the preprocessed and neural MAT files (MAT header export dates set to day 01). The behavioural and sync
  files contain exact session timestamps and are not redistributed (see `NOT_COPIED_release_files.txt`); session months:
  {json.dumps(report['behavioral_dates_ym'])}.

## Privacy
Subject codes only; the behavioural files with exact timestamps are excluded. String scan of the converted MAT files:
{len(report['privacy_flags'])} flagged strings (see code/conversion_report.json).
""",
    changes_note="BIDS conversion of the OSF jq6z4 release (Hoy et al. 2024) for NEMAR (o5c lane A1).")
json.dump(report, open(os.path.join(OUT, "code", "conversion_report.json"), "w"), indent=1, default=str)
print(json.dumps({"recordings": len(Rr), "subjects": len(subs), "hours": hrs, "rt_all": all(r["roundtrip_ok"] for r in Rr), "privacy_flags": report["privacy_flags"][:20], "dates": report["behavioral_dates_ym"]}, indent=1))
print("CONVERT_DONE")
