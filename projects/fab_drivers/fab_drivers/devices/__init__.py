"""One subpackage per piece of equipment.

Each device folder holds its own driver module, its own mock device class, its
own trend page wrapper, and its own PROTOCOL.md saying where every fact in it
came from.

    lakeshore/           218, 224 and 336 temperature monitors
    granville_phillips/  275, 375, 350 and 356 pressure gauges

Read a folder's PROTOCOL.md before changing its driver. Neither of these was
written from a manual, and each PROTOCOL.md opens by saying so.
"""
