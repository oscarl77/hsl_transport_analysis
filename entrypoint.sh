#!/bin/bash

python run_pipeline.py &

streamlit run app/dashboard.py --server.port 8501 --server.address 0.0.0.0