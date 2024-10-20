from apollo import Apollo
import time
from datetime import datetime
import pytz

while True:
    # Get the current time
    cest = pytz.timezone("Europe/Berlin")
    now = datetime.now(cest)
    
    # Check if it's 00:01
    if now.hour == 0 and now.minute == 1:
        Apollo(10000).run(1)
        # Wait for 60 seconds to avoid running multiple times within the same minute
        time.sleep(60)
    
    # Sleep for a short while to avoid overloading the CPU
    time.sleep(30)