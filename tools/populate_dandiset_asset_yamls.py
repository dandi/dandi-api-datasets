#!/usr/bin/env python3
from collections import deque
from contextlib import suppress
import os.path
from pathlib import Path
import sys
import traceback
from dandi.consts import dandiset_metadata_file
from dandi.metadata import nwb2asset
from dandi.models import BareAssetMeta
from dandi.pynwb_utils import validate
from dandi.support.digests import get_digest
from pydantic import ValidationError
import ruamel.yaml


def main():
    yaml = ruamel.yaml.YAML(typ="safe")
    yaml.default_flow_style = False
    for ds in sys.argv[1:]:
        dspath = Path(ds)
        assert dspath.exists(), f"no {ds}"
        if not dspath.is_dir():
            dspath = dspath.parent
        assert dspath.is_dir()
        outdir = Path(dspath.name)
        pynwb_errs = outdir / "NWB-VALIDATION.errors"
        conversion_errs = outdir / "CONVERSION.errors"
        validation_errs = outdir / "VALIDATION.errors"
        with suppress(FileNotFoundError):
            pynwb_errs.unlink()
        with suppress(FileNotFoundError):
            conversion_errs.unlink()
        with suppress(FileNotFoundError):
            validation_errs.unlink()
        for f in iterfiles(dspath):
            if f == dspath / dandiset_metadata_file:
                continue
            relpath = f.relative_to(dspath)
            print("Processing", f)
            sha256_digest = get_digest(f)
            default_metadata = {
                "contentSize": os.path.getsize(f),
                "digest": sha256_digest,
                "digest_type": "SHA256",
                "path": str(f.relative_to(dspath)),
                # "encodingFormat": # TODO
            }
            if f.suffix == ".nwb":
                errors = validate(f)
                if errors:
                    print("PYNWB ERRORS:")
                    for e in errors:
                        print(f" - {e}")
                    with pynwb_errs.open("a") as fp:
                        print(relpath, file=fp)
                        for e in errors:
                            print(f" - {e}", file=fp)
                        print(file=fp)
                try:
                    metadata = nwb2asset(
                        f, digest=sha256_digest, digest_type="SHA256"
                    ).json_dict()
                except Exception as e:
                    print(f"CONVERSION ERROR: {e}")
                    with conversion_errs.open("a") as fp:
                        print(relpath, file=fp)
                        traceback.print_exc(file=fp)
                        print(file=fp)
                    metadata = default_metadata
                else:
                    metadata["path"] = str(relpath)
                    try:
                        BareAssetMeta(**metadata)
                    except ValidationError as e:
                        print(f"VALIDATION ERROR: {e}")
                        with validation_errs.open("a") as fp:
                            print(relpath, file=fp)
                            traceback.print_exc(file=fp)
                            print(file=fp)
            else:
                metadata = default_metadata
            outfile = (outdir / relpath).with_name(f.name + ".yaml")
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
