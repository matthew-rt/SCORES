# Repository file guide

This page covers the files **tracked in git**. (The working tree often
also contains untracked one-off analysis scripts; those are deliberately
not documented.)

## Core model modules

| File | Purpose |
| --- | --- |
| `generation.py` | All generation technology models. See [Generation models](../user-guide/generation.md). |
| `storage.py` | Storage technology models and the `MultipleStorageAssets` portfolio. See [Storage models](../user-guide/storage.md). |
| `system.py` | `ElectricitySystem` / `ElectricitySystemGB` whole-system simulation and heuristic optimisation. See [Electricity systems](../user-guide/system.md). |
| `opt_con_class.py` | The Pyomo linear programme (`System_LinProg_Model`) and result-extraction helpers. See [Linear-programme optimisation](../user-guide/optimisation.md). |
| `aggregatedEVs.py` | Aggregated EV fleet models. See [Electric vehicle fleets](../user-guide/evs.md). |
| `maps.py` | Load-factor estimation and GB maps (currently fails to import — see [Maps and load factors](../user-guide/maps.md)). |
| `fns.py` | Shared helpers: `get_GB_demand` (demand loading), `get_filename` (cache naming), `read_analysis_from_file`, small plotting utilities. |
| `Loaderfunctions.py` | `latlongtosite` (nearest weather site for a coordinate) and `greatcircledistance`. |
| `hydrogenvarstore.py` | Data-only module: cost/efficiency assumptions for PEM, alkaline and solid-oxide electrolysers as small classes. No executable logic. |

## Entry-point and example scripts

| File | Purpose | Status |
| --- | --- | --- |
| `example_scripts.py` | Three original use-cases (generation models, load-factor maps, system optimisation). | Out of date: imports classes that have since been removed. |
| `excelloaderexample.py` | Loads a spreadsheet of real wind farms, maps them to weather sites, builds generator objects. Documents the expected spreadsheet columns in its docstring. | Out of date: calls removed `generation.generatordictionaries`; hard-coded local paths. |
| `GUIrun.py` | Tkinter GUI for configuring and launching runs from an entry spreadsheet. | Out of date: same removed-API and path issues. |
| `LinProgOptExample.py` | Linear-programme run built from real top-10 generator locations. | Out of date: imports removed classes; hard-coded local paths. |
| `loadfactorplotter.py` | Plots load factor vs turbine size from CSVs produced by earlier runs. | Needs `*loadfactors.csv` inputs and `seaborn`. |
| `EntrySpreadsheet.xlsx`, `ExampleEntrySpreadsheet.xlsx` | Input templates for `GUIrun.py` / the Excel-loader workflow. | |

## Userguide_Examples/

Worked examples accompanying `SCORES_User_Guide.pdf`. The most instructive:

| File | Demonstrates |
| --- | --- |
| `simulation_ex.py` | Causal vs non-causal operation of storage + EV fleet ([tutorial 5](../tutorials/05-electric-vehicles.md)). |
| `LinProgExample.py` | Basic LP formulation and solution, plus parameter-based sensitivity (commented). Note: contains some stale attribute/argument names (see [Troubleshooting](troubleshooting.md)). |
| `Pyomo_Example.py` | Minimal standalone Pyomo problem; use to verify your solver installation. |
| `Variable_Parameters.py` | Speed advantage of mutating LP parameters vs reforming the model. |
| `Multiple_Locations.py` | Optimising over many candidate renewable sites. |
| `agg_EV_example.py` | EV fleet definition and sizing. |
| `charger_type.py` | Optimising the V2G vs unidirectional charger mix. |
| `fleetcorrelation.py`, `DDManalysis.py` | Further EV-fleet studies. |
| `2050generator.py` | Building a 2050 generation scenario. |
| `hydrogennogas.py`, `hydrogennogasimportstream.py`, `hydrogengassensitivityunabatedFixed.py`, `unabatedgasinvestigator.py` | Hydrogen vs gas system studies on the LP. |
| `resultplotter.py`, `resultplotternogas.py` | Plotting stored results from the hydrogen/gas studies. |
| `offshoregrossnetcomp.py`, `oldsitescomp.py`, `variableloadfactorinvestigator.py`, `zonalsolargenerator.py` | Site- and load-factor comparison studies. |

## Data and parameters

| Path | Contents |
| --- | --- |
| `data/` | Demand, EV and gas data; per-technology weather folders with `site_locs.csv` and format examples. See [Getting the data](../getting-started/data.md). |
| `data/getting data/` | Legacy scripts for downloading (`getNASA.py`) and converting (`NASA_wind.py`, `NASA_solar.py`) MERRA-2 data. SCORES now uses ERA5 (see [Getting the data](../getting-started/data.md)); these scripts remain useful as templates for the per-site CSV conversion. |
| `data/tidal/` | Tidal site locations, example data, netCDF extraction scripts. |
| `params/` | Cost and technical assumption spreadsheets — **required by default constructors but not tracked in git**. See [Cost parameters](../user-guide/costs.md). |
| `stored_model_runs/` | Cache of generation runs (created at runtime). |
| `log/` | Output folder for analysis text files. |

## Documents

| File | Contents |
| --- | --- |
| `SCORES_User_Guide.pdf` | The original user guide (predates this site). |
| `Getting the Data Required to Run SCORES.pdf` | Step-by-step MERRA-2 download instructions (legacy — SCORES now uses ERA5, see [Getting the data](../getting-started/data.md)). |
| `LinearProgramFormulation.pdf` | Mathematical formulation of the linear programme. |
| `README.md` | Repository readme. |
