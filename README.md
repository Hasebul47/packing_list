Folder layout
  app.py                  <- router (run this)
  gap/gap_app.py          <- GAP module, exposes run(pdf_file)   (converted)
  gap/unified_packing.py  <- original GAP script (kept, still runs standalone)
  vans/vans_app.py        <- put your Vans app.py here, renamed

The router calls run(pdf_file) if the app file defines it; otherwise it runs the
file as a plain script (so Vans works now, before conversion).

Run:  pip install -r requirements.txt && streamlit run app.py
Standalone GAP:  cd gap && streamlit run gap_app.py
