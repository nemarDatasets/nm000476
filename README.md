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
  have no trial events (sub-PFC01's two runs have an events.tsv with only `BAD_nan` rows, see 'NaN samples').
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

## NaN samples in the signal files (checked 19 Oct 2026)

Some signal files store NaN (not-a-number) samples. On 19 Oct 2026 every sample of all 14 recordings was checked (each file read whole with MNE, in time chunks, in a scan Job); 2 recordings hold NaN samples. The data files are unchanged: no sample was replaced, interpolated or cropped, and `raw.get_data()` still returns the NaN values.

Here the NaN samples are isolated single samples (or very short runs) present in all four channels at the same time in the two continuous `acq-raw` exports of sub-PFC01, as released by the authors.

In 2 recordings channels are NaN in part of the recording: 6652 runs of consecutive NaN samples (6649 inside the recording, 2 at the end, 1 at the start; per recording a median 1.14% of the samples; channels most often involved: ch1 (2 recordings), ch2 (2 recordings), ch3 (2 recordings), ch4 (2 recordings)). Each run is now a row of the recording's `events.tsv` with `trial_type` `BAD_nan`, `onset` = first NaN sample / sampling frequency and `duration` = number of NaN samples / sampling frequency (`sample` = index of the first NaN sample, 0-based). 2 events.tsv files were created for this (they hold only BAD_nan rows; these recordings had no events.tsv). Existing rows are unchanged; the rows are sorted by onset. `BAD_nan` is defined in `sub-PFC01/ieeg/sub-PFC01_task-effort_acq-raw_run-1_events.json`, `sub-PFC01/ieeg/sub-PFC01_task-effort_acq-raw_run-2_events.json`.

MNE-BIDS (`read_raw_bids`) turns every events.tsv row into an annotation, and MNE treats annotations whose name starts with `BAD` as bad spans: `raw.get_data(reject_by_annotation='omit')` leaves these samples out, and `mne.Epochs(..., reject_by_annotation=True)` (the default) drops epochs that overlap them. An annotation covers all channels, so a span in which only one channel is NaN is left out for every channel; to keep the other channels, crop or pick channels instead. Filtering does not skip BAD spans by default, so replace or crop NaN samples before filtering.

Per NaN run and per all-NaN channel (recording, sample range, onset and duration in seconds, channels): `code/fix-20261019_nan_spans.tsv`. `code/fix-20261018_nan_scan.json` is the earlier, partial scan of 18 Oct 2026 (it skipped the largest recordings and lists at most 200 spans per recording); it is superseded by the table.
