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
