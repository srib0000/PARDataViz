# TODOs To Get Done

## Turkey week push

* Get the April 28th Dataset. Scans 11 and 12 are best according to David. (Scan 11 isn't in the folder? But I got scans 12, 13, and 14) ✔️
* Solve the polar space issue (scaling and whitespace). ✔️
* Integrate the scansets into the tool. ✔️
* Dynamically add/remove PPI and RHI views. ✔️
* Switching products. Back when we were using matplotlib, it was nice to have a right-click context menu. In VisPy that seems a lot more difficult. I hate to put it buried in the menubar. Need to figure this out. (Implemented by right-clicking on the title of the PPI/RHI plot in the scene) ✔️
* Hook up the volume_slice_selector to the plots. Partially complete! ✔️
* Every time a new volume is loaded, the selected indexes in the volume slice seletor are cleared. This is probably because I recreate it every time the volume changes. ✔️
* Get the "play" button working. ✔️
* Axes and current product label. ✔️
* Hover tooltips for "details-on-demand". ✔️

## Remaining tasks

* Make a cleanup and documentation pass on everything.
* Fix initialization of the slice plots (don't explode when data isn't loaded).
* Fix hardcoded `colormaps.mat` path in slice plot. The slice plot instantiates a ColorMaps object using a path from my machine. The application should have a configuration file that can be edited (build a editor dialog) to configure the path to the colormaps file.
* Fix volume slice selector selection and hover clearing on each volume update (play, forward, back). It should maintain it's state as long as the scan geometry matches.

