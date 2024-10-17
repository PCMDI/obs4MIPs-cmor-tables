import logging
import json
import xcdat as xc
from datetime import datetime
from pcmdi_metrics.utils import check_monthly_time_axis

# Define paths
pin = '/p/user_pub/PCMDIobs/'
cat = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_v20240716.json'

# Set up logging
# Create a unique log filename with timestamp
log_filename = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
# Configure logging: set file, level, format, and force overwrite
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    force=True)

# Create a logger instance
logger = logging.getLogger(__name__)
logger.info("Starting the script")

# Load the catalogue file
with open(cat, 'r') as f:
   dic = json.load(f)

# Get all variables from the catalogue
vars = dic.keys()
logger.info(f"Number of variables: {len(vars)}")

# Iterate through each variable
for v in vars:
    # Get all sources for the current variable
    srcs = dic[v].keys()
    logger.info(f"Processing variable: {v}")

    # Iterate through each source
    for src in srcs:
         # Construct the full path
         pth = pin + dic[v][src]['template']
         logger.info(f"Processing source: {src}, path: {pth}")

         # Open dataset: multi-file or single file
         if '*' in pth:
               fc = xc.open_mfdataset(pth)
               logger.info(f"Opened multi-file dataset: {pth}")
         else:
               fc = xc.open_dataset(pth)
               logger.info(f"Opened single file dataset: {pth}")

         # Check monthly time axis
         try:
               check_monthly_time_axis(fc)
               logger.info(f"Successfully checked monthly time axis for {v} {src}")
         except Exception as e:
               # Log and print any errors encountered
               logger.error(f"Problem with {v} {src} {dic[v][src]['template']}: {str(e)}")
               print(f"Problem with {v} {src} {dic[v][src]['template']}")

         # Close the dataset if it was opened
         if 'fc' in locals():
               fc.close()
               logger.info(f"Closed dataset for {v} {src}")

# Log completion of script
logger.info("Script execution completed")
print('done!')
print(f"Log saved to: {log_filename}")
