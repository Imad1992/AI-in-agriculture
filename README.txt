TRACE Demo, Research Associate Interview Package
==================================================

What's in this folder
----------------------
generate_data.py                  Step 1: creates the synthetic IoT sensor data (shipments.csv, sensor_timeseries.csv)
generate_hyperspectral_images.py  Step 2: creates the hyperspectral checkpoint imaging data
monitoring_analysis.py            Step 3: applies compliance thresholds, builds alerts and the monitoring register
build_dashboard.py                Step 4: combines everything into the final dashboard HTML file

TRACE_demo_dashboard.html         The finished, ready-to-open dashboard (already built, no setup needed)
TRACE_Demo_Explainer.docx         Plain-English guide to the dashboard and dataset, for interview prep

shipments.csv                     Sample output from Step 1 (one row per shipment)
sensor_timeseries.csv             Sample output from Step 1 (one row per 15-minute reading)


Quickest option
----------------
Just double-click TRACE_demo_dashboard.html to open it in your browser. It already works on its own.


To run the full pipeline yourself (e.g. in VS Code)
-----------------------------------------------------
1. Open this folder in VS Code (File > Open Folder).
2. Open a terminal (Terminal > New Terminal) and set up Python:

     python3 -m venv venv
     source venv/bin/activate        (Windows: venv\Scripts\activate)
     pip install pandas numpy scikit-learn

3. Run the four scripts in order:

     python3 generate_data.py
     python3 generate_hyperspectral_images.py
     python3 monitoring_analysis.py
     python3 build_dashboard.py

4. Open the newly rebuilt TRACE_demo_dashboard.html in your browser.

Note: if you edit build_dashboard.py, rerun it afterwards to regenerate the HTML.
Editing the HTML file directly will not survive the next rebuild.
