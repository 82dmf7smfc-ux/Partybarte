"""The parts every driver shares.

    policy.py       decides which commands are allowed to leave the computer
    audit.py        writes every raw frame to a dated log file
    history.py      writes readings to daily CSV files for trending
    mock_serial.py  a fake serial port, so you can work with no hardware
    transport.py    owns the one real serial port and does one exchange at a time
    device.py       the base class a driver builds on, with retries and staleness
    poller.py       reads a set of values on a gentle repeating loop
"""
