"""Two frozen CR12 scanner goals with one scene, controller and camera product."""
from __future__ import annotations


def main():
    from run_cr12_single_view_capture import main as capture_main
    from _cr12_two_view_capture import run_two_capture
    return capture_main(capture_runner=run_two_capture,
        success_label='TWO_VIEW_CAPTURE_INTEGRATION_PASS', entry_source=__file__)


if __name__ == '__main__':
    raise SystemExit(main())
