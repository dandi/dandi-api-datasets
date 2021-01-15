#!/usr/bin/env python3

from pathlib import Path
import sys
from dandi.metadata import migrate2newschema
from dandi.dandiset import Dandiset
from dandi.consts import dandiset_metadata_file
from dandi.utils import yaml_dump
import yaml

if __name__ == "__main__":
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        assert dspath.is_dir()
        dandiset = Dandiset(dspath)
        dandiset_meta = dandiset.metadata
        new_meta = migrate2newschema(dandiset_meta)
        # we still would get empty containers such as
        # identifier: {}
        # TODO: this all should be in dandi-cli
        new_meta_json = new_meta.json(exclude_unset=True, exclude_none=True)
        newds_path = Path(dspath.name)
        if not newds_path.exists():
            newds_path.mkdir()
        newmeta_path = newds_path / dandiset_metadata_file
        newmeta_path.write_text(
            yaml_dump(yaml.load(new_meta_json, Loader = yaml.BaseLoader))
        )
        print(f"Dumped {newmeta_path}")
