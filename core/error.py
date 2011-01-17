import logging

# from scapy
log_andro = logging.getLogger("andro")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log_andro.addHandler(console_handler)
log_runtime = logging.getLogger("andro.runtime")          # logs at runtime
log_interactive = logging.getLogger("andro.interactive")  # logs in interactive functions
log_loading = logging.getLogger("andro.loading")          # logs when loading andro 

def warning(x):
   log_runtime.warning(x)
