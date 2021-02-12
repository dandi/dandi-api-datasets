#!/usr/bin/env python3
from collections import deque
import os.path
from pathlib import Path
import sys
from dandi.consts import dandiset_metadata_file
from dandi.metadata import nwb2asset
from dandi.support.digests import Digester
import ruamel.yaml


def main():
    digester = Digester(["sha256"])
    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        assert dspath.is_dir()
        for f in iterfiles(dspath):
            if f == dspath / dandiset_metadata_file:
                continue
            print("Processing", f)
            sha256_digest = digester(f)["sha256"]
            try:
                metadata = nwb2asset(
                    f, digest=sha256_digest, digest_type="SHA256"
                ).json_dict()
            except Exception:
                metadata = {
                    "contentSize": os.path.getsize(f),
                    "digest": sha256_digest,
                    "digest_type": "SHA256",
                    "path": str(f.relative_to(dspath)),
                    # "encodingFormat": # TODO
                }
            else:
                metadata["path"] = str(f.relative_to(dspath))
            outfile = Path(dspath.name, f.relative_to(dspath))
            outfile = outfile.with_name(outfile.name + ".yaml")
            outfile.parent.mkdir(parents=True, exist_ok=True)
            with outfile.open("w") as fp:
                yaml.dump(metadata, fp)


def iterfiles(dirpath):
    dirs = deque([dirpath])
    while dirs:
        d = dirs.popleft()
        for p in d.iterdir():
            if p.name.startswith("."):
                continue
            if p.is_dir():
                dirs.append(p)
            else:
                yield p


if __name__ == "__main__":
    main()
