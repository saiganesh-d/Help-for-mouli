# the newer, multi-bus reader (CAN + Ethernet + …)
pip install vblf          # PyPI project “vblf”

# ⬑ if that wheel won’t build on your platform, fall back to python-can
pip install python-can


#!/usr/bin/env python3
"""
blf_scan.py  –  list frame type + attribute names for every object in a BLF.

  $ python blf_scan.py bigfile.blf --limit 20

* Streams the file – only the current object is in memory.
* Works with either the 'vblf' or the 'python-can' backend.
"""

import argparse
import importlib
import sys
from typing import Iterable, List


def iter_blf(path: str):
    """
    Yield (frame_type:str, obj) tuples using whichever BLF backend is available.
    Priority: vblf  ➜  python-can.
    """
    if importlib.util.find_spec("vblf"):
        from vblf.reader import BlfReader

        with BlfReader(path) as rd:        # generator – handles > 2 GB easily
            for obj in rd:
                frame_type = obj.header.base.object_type.name
                yield frame_type, obj

    elif importlib.util.find_spec("can"):
        import can                          # python-can
        from can.io.blf import BLFReader

        with BLFReader(path) as rd:
            for msg in rd:
                # python-can only returns CAN / CAN FD messages
                frame_type = "CAN-FD" if msg.is_fd else "CAN"
                yield frame_type, msg
    else:
        sys.exit("❌  Neither 'vblf' nor 'python-can' is installed.")


def public_attrs(obj) -> List[str]:
    "Return a list of attribute names that don't start with '_'"
    return [a for a in dir(obj) if not a.startswith('_')]


def main():
    ap = argparse.ArgumentParser(description="Quick BLF scanner")
    ap.add_argument("blf", help="Path to .blf file")
    ap.add_argument("--limit", type=int, default=0,
                    help="Stop after N frames (0 = no limit)")
    args = ap.parse_args()

    for i, (ftype, obj) in enumerate(iter_blf(args.blf), 1):
        attrs = public_attrs(obj)
        print(f"[{i:>6}] {ftype:12}  attrs={attrs[:8]}{' …' if len(attrs) > 8 else ''}")

        if args.limit and i >= args.limit:
            break


if __name__ == "__main__":
    main()




#!/usr/bin/env python3
"""
mf4_scan.py  –  list every channel in a multi-GB MF4 file with bus-type guess.

Usage:
    $ python mf4_scan.py mylog.mf4 --limit 10
"""

import argparse
from datetime import datetime
from pathlib import Path

from asammdf import MDF, Signal

BUS_TAGS = {
    "CAN":     ("CAN_", "CAN "),     # CAN/CAN FD
    "LIN":     ("LIN_", "LIN "),     # LIN
    "FlexRay": ("FR_",),             # FlexRay
    "ETH":     ("ETH", "ETHERNET"),  # SOME-IP / raw Eth
}

def guess_bus(channel_group_name: str) -> str | None:
    upper = channel_group_name.upper()
    for bus, prefixes in BUS_TAGS.items():
        if any(upper.startswith(p) for p in prefixes):
            return bus
    return None


def scan_mf4(path: Path, limit: int | None = None):
    with MDF(path, memory="minimal") as mdf:          # <—— no full file in RAM
        for cg_index, cg in enumerate(mdf.groups, start=1):
            bus = guess_bus(cg.name or "")
            for ch_index, ch in enumerate(cg.channels, start=1):
                sig: Signal = mdf.get_signal(ch)      # lazy – data not loaded yet
                start, stop = sig.timestamps[[0, -1]]
                print(f"[CG{cg_index:03}.{ch_index:04}] "
                      f"{sig.name:30} "
                      f"({sig.unit or '—':8})  "
                      f"samples={len(sig):7d}  "
                      f"{datetime.utcfromtimestamp(start):%H:%M:%S.%f}–"
                      f"{datetime.utcfromtimestamp(stop):%H:%M:%S.%f}  "
                      f"{bus or ''}")
                if limit and cg_index >= limit:
                    return


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mf4", type=Path, help="Path to .mf4 file")
    ap.add_argument("--limit", type=int, help="Stop after N channel-groups")
    args = ap.parse_args()
    scan_mf4(args.mf4, args.limit)
