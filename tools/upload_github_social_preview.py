from __future__ import annotations

import argparse
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = REPO_ROOT / "docs" / "assets" / "social-preview.png"
DEFAULT_PROFILE_DIR = REPO_ROOT / ".local" / "browser" / "github-social-preview"
DEFAULT_REPOSITORY = "YSCJRH/skylattice"
MAX_SOCIAL_PREVIEW_BYTES = 1_000_000
MIN_SOCIAL_PREVIEW_WIDTH = 640
MIN_SOCIAL_PREVIEW_HEIGHT = 320


@dataclass(frozen=True)
class ImageCheck:
    path: Path
    width: int
    height: int
    size_bytes: int


def parse_repository(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise argparse.ArgumentTypeError("repository must look like owner/name")
    return value


def _read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("image must be a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def validate_social_preview(path: Path) -> ImageCheck:
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"social preview image does not exist: {resolved}")
    width, height = _read_png_dimensions(resolved)
    size_bytes = resolved.stat().st_size
    if size_bytes > MAX_SOCIAL_PREVIEW_BYTES:
        raise ValueError(f"social preview image must be under 1 MB, got {size_bytes} bytes")
    if width < MIN_SOCIAL_PREVIEW_WIDTH or height < MIN_SOCIAL_PREVIEW_HEIGHT:
        raise ValueError(
            "social preview image must be at least "
            f"{MIN_SOCIAL_PREVIEW_WIDTH}x{MIN_SOCIAL_PREVIEW_HEIGHT}, got {width}x{height}"
        )
    return ImageCheck(path=resolved, width=width, height=height, size_bytes=size_bytes)


def _playwright_import():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is required for social preview upload automation.\n"
            "Install it with:\n"
            "  python -m pip install -e .[automation]\n"
            "  python -m playwright install chromium"
        ) from exc
    return sync_playwright, PlaywrightTimeoutError


def _wait_for_settings_page(page, repository: str, timeout_ms: int, auth_timeout_ms: int) -> None:
    settings_url = f"https://github.com/{repository}/settings"
    page.goto(settings_url, wait_until="domcontentloaded", timeout=timeout_ms)
    social_heading = page.get_by_text("Social preview", exact=True).first
    announced_auth = False
    remaining_ms = auth_timeout_ms
    while remaining_ms > 0:
        try:
            social_heading.wait_for(timeout=1_000)
            return
        except Exception:
            if any(marker in page.url for marker in ["/login", "/session", "/sessions", "/two-factor"]):
                if not announced_auth:
                    print("GitHub login or two-factor verification is required in the opened browser window.")
                    print("The script will continue after the repository Settings page is visible.")
                    announced_auth = True
            elif f"/{repository}/settings" not in page.url:
                try:
                    page.goto(settings_url, wait_until="domcontentloaded", timeout=timeout_ms)
                except Exception:
                    pass
            page.wait_for_timeout(1_000)
            remaining_ms -= 2_000
    raise TimeoutError("timed out waiting for GitHub Settings > Social preview after authentication")


def _try_set_existing_file_input(page, image_path: Path) -> bool:
    inputs = page.locator("input[type='file']")
    for index in range(inputs.count()):
        candidate = inputs.nth(index)
        accept = candidate.get_attribute("accept") or ""
        name = candidate.get_attribute("name") or ""
        aria = candidate.get_attribute("aria-label") or ""
        marker = " ".join([accept, name, aria]).lower()
        if "image" in marker or "social" in marker or ".png" in marker:
            candidate.set_input_files(str(image_path))
            return True
    return False


def _click_with_file_chooser(page, locator, image_path: Path, timeout_error, timeout_ms: int) -> bool:
    try:
        with page.expect_file_chooser(timeout=timeout_ms) as chooser:
            locator.click(timeout=timeout_ms)
        chooser.value.set_files(str(image_path))
        return True
    except timeout_error:
        return False


def _click_social_preview_edit(page, timeout_error, timeout_ms: int) -> None:
    social_heading = page.get_by_text("Social preview", exact=True).first
    social_heading.wait_for(timeout=timeout_ms)
    social_heading.scroll_into_view_if_needed(timeout=timeout_ms)

    containers = [
        social_heading.locator("xpath=ancestor::*[contains(@class, 'Box')][1]"),
        social_heading.locator("xpath=ancestor::section[1]"),
        social_heading.locator("xpath=ancestor::div[1]"),
    ]
    button_names = re.compile(r"edit|change|upload|replace", re.IGNORECASE)
    for container in containers:
        try:
            button = container.get_by_role("button", name=button_names).first
            button.wait_for(timeout=2_000)
            button.click(timeout=timeout_ms)
            return
        except timeout_error:
            continue

    for name in ["Edit", "Change", "Upload", "Replace"]:
        try:
            page.get_by_role("button", name=re.compile(name, re.IGNORECASE)).first.click(timeout=timeout_ms)
            return
        except timeout_error:
            continue
    raise RuntimeError("could not find the Social preview edit/upload control")


def _upload_social_preview(page, image_path: Path, timeout_error, timeout_ms: int) -> None:
    social_heading = page.get_by_text("Social preview", exact=True).first
    social_heading.wait_for(timeout=timeout_ms)
    social_heading.scroll_into_view_if_needed(timeout=timeout_ms)

    if _try_set_existing_file_input(page, image_path):
        return

    _click_social_preview_edit(page, timeout_error, timeout_ms)
    page.wait_for_timeout(500)

    if _try_set_existing_file_input(page, image_path):
        return

    upload_text = re.compile(r"upload|change|replace|select", re.IGNORECASE)
    candidates = [
        page.get_by_role("menuitem", name=upload_text).first,
        page.get_by_role("button", name=upload_text).first,
        page.get_by_text(upload_text).first,
    ]
    for candidate in candidates:
        if _click_with_file_chooser(page, candidate, image_path, timeout_error, timeout_ms):
            return

    raise RuntimeError("could not attach the social preview image through the GitHub UI")


def _click_save_if_present(page, timeout_error, timeout_ms: int) -> bool:
    save_name = re.compile(r"^(save|update|apply)( changes)?$|^set new social preview$", re.IGNORECASE)
    for role in ["button", "menuitem"]:
        try:
            button = page.get_by_role(role, name=save_name).first
            button.wait_for(timeout=2_000)
            if button.is_visible():
                button.click(timeout=timeout_ms)
                return True
        except timeout_error:
            continue
    return False


def upload_social_preview(
    repository: str,
    image_path: Path,
    profile_dir: Path,
    headless: bool,
    timeout_ms: int,
    auth_timeout_ms: int,
) -> None:
    sync_playwright, timeout_error = _playwright_import()
    image = validate_social_preview(image_path)
    profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            str(profile_dir),
            headless=headless,
            accept_downloads=False,
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        try:
            _wait_for_settings_page(page, repository, timeout_ms, auth_timeout_ms)
            _upload_social_preview(page, image.path, timeout_error, timeout_ms)
            page.wait_for_timeout(3_000)
            _click_save_if_present(page, timeout_error, timeout_ms)
            page.wait_for_timeout(3_000)
            print(
                "Uploaded GitHub social preview candidate: "
                f"{image.path} ({image.width}x{image.height}, {image.size_bytes} bytes)"
            )
            print("Verify the repository header after GitHub finishes processing the image.")
        finally:
            try:
                page.screenshot(path=str(profile_dir / "last-upload-state.png"), full_page=True)
            except Exception:
                pass
            browser.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload the repository social preview image through GitHub Settings.")
    parser.add_argument("--repository", type=parse_repository, default=DEFAULT_REPOSITORY)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--timeout-ms", type=int, default=30_000)
    parser.add_argument("--auth-timeout-ms", type=int, default=600_000)
    parser.add_argument("--headless", action="store_true", help="Run without a visible browser window.")
    parser.add_argument("--check-only", action="store_true", help="Validate the image and print upload settings.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    check = validate_social_preview(args.image)
    if args.check_only:
        print(f"repository: {args.repository}")
        print(f"image: {check.path}")
        print(f"dimensions: {check.width}x{check.height}")
        print(f"size_bytes: {check.size_bytes}")
        print(f"profile_dir: {args.profile_dir.resolve()}")
        return 0
    upload_social_preview(
        repository=args.repository,
        image_path=check.path,
        profile_dir=args.profile_dir,
        headless=args.headless,
        timeout_ms=args.timeout_ms,
        auth_timeout_ms=args.auth_timeout_ms,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
