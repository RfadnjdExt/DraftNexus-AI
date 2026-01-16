import streamlit as st
import sys
import os

# Add the current directory to python path to allow imports from scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.data_entry_app import main

if __name__ == "__main__":
    main()
