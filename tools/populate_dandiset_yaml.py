#!/usr/bin/env python3

from pathlib import Path
import sys
from dandi.dandiset import Dandiset
from dandi.consts import dandiset_metadata_file
from dandi.models import DandisetMeta
import traceback

if __name__ == "__main__":
    ok = True
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        print(f"{dspath}: ", end='')
        assert dspath.is_dir()
        newds_path = Path(dspath.name)
        newmeta_path = newds_path / dandiset_metadata_file
        err_path = newds_path / "EXCEPTION"
        for p in newmeta_path, err_path:
            if p.exists():
                p.unlink()

        if not newds_path.exists():
            newds_path.mkdir()

        dandiset = Dandiset(dspath)
        dandiset_meta = dandiset.metadata
        try:
            DandisetMeta.validate(dandiset_meta)
            print("VALID ")
        except Exception as exc:
            traceback.print_exc(file=err_path.open('w'))
            print(f"EXCEPTION ({err_path}) - {exc}".rstrip())
            ok = False
    sys.exit(0 if ok else 1)
