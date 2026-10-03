import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_checksum_buffers_survive_debug_allocator(tmp_path: Path) -> None:
    script = textwrap.dedent("""
        from concurrent.futures import ThreadPoolExecutor
        import gc
        from importlib.machinery import EXTENSION_SUFFIXES

        import cchecksum._checksum as native
        from cchecksum import to_checksum_address, to_checksum_address_many
        from eth_utils import to_checksum_address as reference

        assert any(native.__file__.endswith(suffix) for suffix in EXTENSION_SUFFIXES)
        addresses = [f"0x{i:040x}" for i in range(256)] + [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "C02AAA39B223FE8D0A0E5C4F27EAD9083C756CC2",
        ]
        expected = [reference(address) for address in addresses]

        def check(_):
            assert [to_checksum_address(address) for address in addresses] == expected
            assert to_checksum_address_many(addresses) == expected
            assert to_checksum_address_many(
                [bytes.fromhex(address.removeprefix("0x")) for address in addresses]
            ) == expected
            gc.collect()

        with ThreadPoolExecutor(max_workers=8) as workers:
            list(workers.map(check, range(32)))
        """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "PYTHONMALLOC": "debug", "PYTHONFAULTHANDLER": "1"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
