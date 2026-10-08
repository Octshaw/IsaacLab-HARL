"""Pure argument preparation for this project's Windows Kit entry points.

This module neither imports the simulator nor selects a runtime device.  The
returned backend is a request; Kit's same-run log must confirm the actual API.
"""

from __future__ import annotations

import sys


_D3D12_ARG = "--/app/vulkan=false"
_BACKEND_REQUESTS = {"--vulkan": "Vulkan", "--/app/vulkan=true": "Vulkan", _D3D12_ARG: "D3D12"}
_KIT_USAGE = 'Use one --kit_args="--/app/vulkan=false" or --kit_args="--/app/vulkan=true" argument.'


def _looks_like_backend_option(token: str) -> bool:
    """Recognize backend spellings needing review without banning other Kit args."""
    option = token.strip("\"'").lower().split("=", 1)[0]
    return option in {
        "--vulkan", "--no-vulkan", "--no_vulkan", "--/app/vulkan", "/app/vulkan",
        "--d3d12", "--d3d11", "--dx12", "--directx", "--directx12",
        "--graphics-api", "--graphics_api", "--graphicsapi", "--/app/graphicsapi",
        "--/renderer/backend", "--/renderer/graphicsapi",
    }


def _check_original_argv(argv: list[str]) -> None:
    """Catch parse_known_args leakage and repeated options hidden by argparse."""
    occurrences = 0
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--kit_args":
            occurrences += 1
            if index + 1 >= len(argv):
                raise ValueError(f"--kit_args requires a value. {_KIT_USAGE}")
            # Its entire following argv element is the Kit payload, not a bare
            # backend option. AppLauncher later applies str.split() to it.
            index += 2
            continue
        if token.startswith("--kit_args="):
            occurrences += 1
        elif _looks_like_backend_option(token):
            raise ValueError(
                f"Bare backend option {token!r} is not accepted by the project entry point; "
                f"it must not leak into Hydra arguments. {_KIT_USAGE}"
            )
        index += 1
    if occurrences > 1:
        raise ValueError(
            "Repeated --kit_args options may hide an earlier backend choice during argument parsing. "
            f"Combine the Kit options into one value. {_KIT_USAGE}"
        )


def prepare_windows_runtime_args(
    args: object, original_argv: list[str] | tuple[str, ...] | None = None
) -> dict[str, object]:
    """Prepare ``args.kit_args`` and return JSON-safe request provenance.

    Non-Windows calls leave the namespace untouched and add no validation rules.
    On Windows, validation completes before the sole mutation (``kit_args``).
    Token recognition deliberately follows AppLauncher's plain ``str.split``;
    the original string and its unrelated quoting/spacing are never rebuilt.
    ``original_argv`` should be captured before any Hydra/Kit argv rewriting.
    """
    argv = list(sys.argv if original_argv is None else original_argv)
    original = getattr(args, "kit_args", "")
    record: dict[str, object] = {
        "original_argv": argv,
        "original_kit_args": original,
        "final_kit_args": original,
        "source": "non_windows_unchanged",
        "requested_backend": None,
        "utf8_mode": sys.flags.utf8_mode,
        "platform": sys.platform,
    }
    if sys.platform != "win32":
        return record

    if sys.flags.utf8_mode != 1:
        raise RuntimeError(
            "Windows runtime startup requires UTF8 mode 1 before Python starts. "
            "Use D:\\miniconda3\\Scripts\\conda.exe run -p C:\\isaacenvs\\isaac45_harl "
            "python <entry.py> <args>, or start the selected Python with -X utf8. "
            "Changing PYTHONUTF8 inside this running process cannot enable its UTF8 mode."
        )
    if not isinstance(original, str):
        raise ValueError(f"kit_args must be a string. {_KIT_USAGE}")
    _check_original_argv(argv)

    selected: set[str] = set()
    for token in original.split():
        if token in _BACKEND_REQUESTS:
            selected.add(_BACKEND_REQUESTS[token])
        elif _looks_like_backend_option(token):
            raise ValueError(f"Unsupported or ambiguous backend spelling {token!r}. {_KIT_USAGE}")
    if len(selected) > 1:
        raise ValueError(
            "Conflicting Vulkan and D3D12 requests in kit_args; "
            f"the project does not use last-option-wins. {_KIT_USAGE}"
        )

    if selected:
        backend = next(iter(selected))
        source = "explicit"
        final = original
    else:
        backend = "D3D12"
        source = "windows_default"
        separator = "" if not original or original[-1].isspace() else " "
        final = original + separator + _D3D12_ARG
        setattr(args, "kit_args", final)
    record.update(final_kit_args=final, source=source, requested_backend=backend)
    return record
