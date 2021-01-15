#!/usr/bin/env python3

from pathlib import Path
import sys
from dandi.metadata import migrate2newschema
from dandi.dandiset import Dandiset
from dandi.consts import dandiset_metadata_file
from dandi.utils import yaml_dump
import yaml
import traceback

if __name__ == "__main__":
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        assert dspath.is_dir()
        newds_path = Path(dspath.name)
        err_path = newds_path / "EXCEPTION"
        if err_path.exists():
            err_path.unlink()
        if not newds_path.exists():
            newds_path.mkdir()
        dandiset = Dandiset(dspath)
        dandiset_meta = dandiset.metadata
        try:
            new_meta = migrate2newschema(dandiset_meta)
            # we still would get empty containers such as
            # identifier: {}
            # TODO: this all should be in dandi-cli
            new_meta_json = new_meta.json(exclude_unset=True, exclude_none=True)
            newmeta_path = newds_path / dandiset_metadata_file
            newmeta_path.write_text(
                yaml_dump(yaml.load(new_meta_json, Loader = yaml.BaseLoader))
            )
            print(f"{dspath}: OK. Dumped {newmeta_path}")
        except Exception as exc:
            traceback.print_exc(file=err_path.open('w'))
            sys.stderr.write(f"{dspath}: EXCEPTION ({err_path}) - {exc}".rstrip() + "\n")
