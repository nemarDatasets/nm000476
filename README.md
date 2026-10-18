[![DOI](https://img.shields.io/badge/DOI-10.82901%2Fnemar.nm000476-blue)](https://doi.org/10.82901/nemar.nm000476)

# Hoy et al. 2024: basal ganglia and prefrontal LFP during effort-based decisions (intraoperative DBS recordings)

5 subjects, 14 recordings, 3.90 h. Released by the authors on OSF (doi:10.17605/OSF.IO/JQ6Z4, CC-BY-4.0).

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
  {"PFC01_behavioral_data_run1.mat": "2020-06-01", "PFC01_behavioral_data_run2.mat": "2020-06-01", "PFC03_behavioral_data_run1.mat": "2019-12-01", "PFC03_behavioral_data_run2.mat": "2019-12-01", "PFC04_behavioral_data_run1.mat": "2019-09-01", "PFC04_behavioral_data_run2.mat": "2019-09-01", "PFC05_behavioral_data_run1.mat": "2019-09-01", "PFC05_behavioral_data_run2.mat": "2019-09-01", "PMC10_behavioral_data_run1.mat": "2020-01-01", "PMC10_behavioral_data_run2.mat": "2020-01-01"}.

## Privacy
Subject codes only; the behavioural files with exact timestamps are excluded. String scan of the converted MAT files:
12 flagged strings (see code/conversion_report.json).

## Units when reading with MNE (added 2026-10-17, version 1.0.3)

The release does not state the physical unit of the signal values, so the BrainVision headers and channels.tsv give
the unit `n/a` (resolution 1) and the values are the release's numbers, unchanged. MNE and MNE-BIDS read a channel
with unit `n/a` as volts with scale 1: `raw.get_data()` returns the stored numbers as they are, labelled V. If the
numbers are microvolt-sized, anything that assumes volts (plot scalings, rejection thresholds, µV conversions) sees
them 1e6 times too large. In the 2026-10-17 check the channels had a robust SD of about 0.009-0.011 in the runs read, so these numbers are not microvolts either. No unit is assigned here because the source does not state one; treat the values as the
release's numbers in an unknown unit.

## NaN samples in the signal files (checked 18 Oct 2026)

Some signal files store NaN (not-a-number) samples. A scan of 14 of the 14 recordings (whole files read with MNE on 18 Oct 2026; all recordings) found them in 2 recordings. Both MNE-BIDS and EEGDash load these files; `get_data()` returns the NaN values.

In 2 recordings channels are NaN only in part of the recording (399 spans inside the recording, 1 spans at the start; median 1.14% of the samples; channels most often affected: ch1 (2), ch2 (2), ch3 (2), ch4 (2)). Examples: `sub-PFC01_task-effort_acq-raw_run-1_ieeg.vhdr` ch1, ch2, ch3, ch4 samples 25-26 (+4775 more spans); `sub-PFC01_task-effort_acq-raw_run-2_ieeg.vhdr` ch1, ch2, ch3, ch4 samples 0-1 (+1875 more spans). These samples cannot be restored from the release; crop them or replace them (e.g. `numpy.nan_to_num`, interpolation) before filtering. The data files are unchanged.

Per-recording details (channels, NaN sample spans): `code/fix-20261018_nan_scan.json`.
