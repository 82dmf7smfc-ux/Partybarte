"""A library of small, read-only monitoring drivers for fab equipment.

Every driver in this library shares one core. The core handles the parts that
are the same no matter which box you are talking to: opening exactly one serial
port, sending a frame and waiting for a reply, retrying a quiet device, writing
every raw frame to an audit file, and trending readings into daily CSV files.

A driver adds only the part that is different: how that vendor frames a message,
and which commands are safe to send.

Read the project read me before connecting anything to real equipment.
"""
