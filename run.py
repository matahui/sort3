import os
import sys
import streamlit.web.cli as stcli

if __name__ == '__main__':
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the application directory
    os.chdir(application_path)
    
    # Set up the command line arguments for Streamlit
    sys.argv = ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=localhost"]
    
    # Run the Streamlit application
    sys.exit(stcli.main()) 