#!/usr/bin/env python3
"""
LuaTools Fluenty Patcher - LuaTools 1.3.2 / LTSP v2.2

Patches the LuaTools Steam store-page frontend (luatools.js) so its buttons
survive themes (like Fluenty) that hide the SteamDB button row: on a store
app page whose normal button container is missing or hidden, the buttons are
placed into a fixed "restart pill" instead.

Also replaces the external Font Awesome loader with embedded SVG icons for
LuaTools menus, dialogs, and status indicators. No icon-font download is
needed. Existing placement patches and original .bak backups are preserved.

Layout notes for LuaTools 1.3.2 (from its source):
  * The frontend is no longer bundled with the app or dropped into Steam's
    steamui folder. It is downloaded from GitHub releases (madoiscool/LTSP)
    into %APPDATA%\\LuaToolsGui\\plugin\\public\\luatools.js
    (fallback: %APPDATA%\\LuaToolsGui\\plugin\\luatools.js).
  * The LuaTools app reads luatools.js from disk into memory at startup and
    injects it into Steam store tabs over CDP. After patching you must exit
    LuaTools from the tray and start it again (a Steam restart is NOT needed),
    then refresh/reopen the store pages.
  * LuaTools auto-updates this file when a new plugin release appears, which
    overwrites the patch - just re-run this script afterwards.

Usage:
    python LuaTools-Fluenty-Theme-Patch-fixed.py [path\\to\\luatools.js]

Without an argument, the active frontend is auto-detected using the same
lookup order the LuaTools 1.3.2 injector uses. If the plugin is not installed
yet, nothing is patched automatically - install it from the LuaTools app
(Plugin page) first, or pass the path explicitly.
"""

import json
import os
import shutil
import sys

# --- Target discovery ---------------------------------------------------------
# Mirrors LuaTools 1.3.2's CefInjectorService.FindLuaToolsJs: these two, in this
# order. If neither exists the injector loads no frontend at all, so we do NOT
# fall back to old Steam/Millennium copies (they can be inactive/disabled, and
# patching them would report success while changing nothing the user sees).
APPDATA = os.path.expandvars(r"%APPDATA%")

CANDIDATES = [
    os.path.join(APPDATA, "LuaToolsGui", "plugin", "public", "luatools.js"),
    os.path.join(APPDATA, "LuaToolsGui", "plugin", "luatools.js"),
]

TARGET = sys.argv[1] if len(sys.argv) > 1 else None

if not TARGET:
    for path in CANDIDATES:
        if os.path.isfile(path):
            TARGET = path
            break


def manifest_tag_for(target):
    """Best-effort: report the installed plugin release tag from installed.json."""
    candidates = [
        os.path.join(os.path.dirname(target), "installed.json"),
        os.path.join(os.path.dirname(os.path.dirname(target)), "installed.json"),
    ]
    for m in candidates:
        try:
            with open(m, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                tag = data.get("Tag") or data.get("tag")
                if tag:
                    return tag
        except (OSError, ValueError):
            continue
    return None


print("============================================")
print("   LuaTools Fluenty Patcher (LuaTools 1.3.2+)")
print("============================================\n")

if not TARGET or not os.path.isfile(TARGET):
    if TARGET and not os.path.isfile(TARGET):
        print(f"[!] The path you supplied is not a file: {TARGET}")
        print("    No other file was selected in its place. Nothing was changed.")
        sys.exit(1)
    print("[!] Could not auto-detect the active LuaTools frontend.")
    print("    For LuaTools 1.3.2+, install the plugin from the LuaTools app")
    print("    (Plugin page) and run LuaTools once, so it downloads")
    print("    %APPDATA%\\LuaToolsGui\\plugin\\public\\luatools.js")
    while True:
        custom_input = input("    Path to luatools.js (or Enter to cancel): ").strip().strip('"')
        if not custom_input:
            print("\n[CANCELLED] Exiting.")
            sys.exit(1)
        if os.path.isfile(custom_input):
            TARGET = custom_input
            break
        print(f"\n    [!] File not found: {custom_input}\n")

print(f"[+] Target found : {TARGET}")
tag = manifest_tag_for(TARGET)
if tag:
    print(f"[+] Plugin tag   : {tag}")
print()

with open(TARGET, "rb") as f:
    raw_bytes = f.read()

crlf_mode = b"\r\n" in raw_bytes
try:
    content = raw_bytes.decode("utf-8")  # strict: never silently mangle bytes
except UnicodeDecodeError as e:
    print(f"[!] The file is not valid UTF-8 ({e}). No changes were made.")
    sys.exit(1)
normalized_content = content.replace("\r\n", "\n")

BACKUP = TARGET + ".bak"

# --- Patch definition ---------------------------------------------------------
#
# Anchor (present in the current LTSP v2.2 frontend, exactly once): the tail of
# the else-branch in addLuaToolsButton() that picks the normal button container.
# The injected block creates a fixed "restart pill" on store app pages when that
# container is missing/hidden, points targetContainer at it, and relocates any
# buttons that were already inserted into the hidden container (the theme can
# hide the container before OR after the buttons are first inserted). A hidden
# reference anchor inside the pill keeps the button-creation code below from
# copying its classes off the Restart button (its querySelector("a") would
# otherwise return it), which would leak .luatools-restart-button onto the
# LuaTools button.

P1_SENTINEL = "// [FLUENTY-PATCH-1] split placement"

P1_OLD = """        document.querySelector(".steamdb-buttons") ||
        document.querySelector("[data-steamdb-buttons]") ||
        document.querySelector(".apphub_OtherSiteInfo");
    }"""

# The pill block exactly as the ORIGINAL LuaTools-Fluenty patch injected it
# (used to migrate an already-patched file to this revision).
P1_OLD_TAIL = """

      // [FLUENTY-PATCH-1] split placement
      var isStorePage = window.location.href.includes("store.steampowered.com/app/");
      if (isStorePage && (!targetContainer || targetContainer.offsetParent === null)) {
        if (!document.querySelector(".luatools-restart-pill")) {
          var pill = document.createElement("div");
          pill.className = "luatools-restart-pill";
          pill.style.cssText = "position:fixed;top:75px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:6px;";
          document.body.appendChild(pill);
        }
        targetContainer = document.querySelector(".luatools-restart-pill");
      }
"""

P1_NEW = """        document.querySelector(".steamdb-buttons") ||
        document.querySelector("[data-steamdb-buttons]") ||
        document.querySelector(".apphub_OtherSiteInfo");
    }

      // [FLUENTY-PATCH-1] split placement
      var isStorePage = window.location.href.includes("store.steampowered.com/app/");
      if (isStorePage && (!targetContainer || targetContainer.offsetParent === null)) {
        var hiddenRow = targetContainer;
        if (!document.querySelector(".luatools-restart-pill")) {
          var pill = document.createElement("div");
          pill.className = "luatools-restart-pill";
          pill.style.cssText = "position:fixed;top:75px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:6px;";
          document.body.appendChild(pill);
        }
        targetContainer = document.querySelector(".luatools-restart-pill");
        // Hidden reference anchor: the button-creation code below picks its
        // classes from the container's first <a>; without this, that would be
        // the Restart button, leaking .luatools-restart-button onto the
        // LuaTools button.
        if (!targetContainer.querySelector("[data-luatools-pill-ref]")) {
          var pillRef = document.createElement("a");
          pillRef.className = "btnv6_blue_hoverfade btn_medium";
          pillRef.href = "#";
          pillRef.style.display = "none";
          pillRef.setAttribute("data-luatools-pill-ref", "1");
          targetContainer.insertBefore(pillRef, targetContainer.firstChild);
        }
        // Relocate buttons already inserted into the (hidden) normal container,
        // so they don't stay invisible inside it. Steam fills that row
        // asynchronously, so the buttons may have been created while it was
        // still empty - then the LuaTools button copied the Restart button's
        // classes (it was the only <a> around) and wrongly carries
        // .luatools-restart-button. Strip the foreign role class while moving.
        var existingRestartBtn = document.querySelector(".luatools-restart-button");
        if (existingRestartBtn && existingRestartBtn.parentElement !== targetContainer) {
          existingRestartBtn.className = existingRestartBtn.className
            .split(/\\s+/)
            .filter(function (c) { return c !== "luatools-button"; })
            .join(" ");
          targetContainer.appendChild(existingRestartBtn);
        }
        var existingLuaBtn = document.querySelector(".luatools-button");
        if (existingLuaBtn && existingLuaBtn.parentElement !== targetContainer) {
          existingLuaBtn.className = existingLuaBtn.className
            .split(/\\s+/)
            .filter(function (c) { return c !== "luatools-restart-button"; })
            .join(" ");
          targetContainer.appendChild(existingLuaBtn);
        }
        // The LuaTools button is inserted asynchronously (a backend presence
        // check gates it). If that check resolves only after this row got
        // hidden, its callback still appends the button to the row it
        // captured - and nothing re-runs afterwards (the page's own mutation
        // observer sees the button exists and stays quiet). Watch the hidden
        // row and pull our buttons into the pill when that happens.
        if (hiddenRow) {
          var pillPull = function () {
            var pillEl = document.querySelector(".luatools-restart-pill");
            if (!pillEl) return;
            var pullBtn = function (sel, foreign) {
              var btn = document.querySelector(sel);
              if (btn && btn.parentElement !== pillEl) {
                btn.className = btn.className
                  .split(/\\s+/)
                  .filter(function (c) { return c !== foreign; })
                  .join(" ");
                pillEl.appendChild(btn);
              }
            };
            pullBtn(".luatools-restart-button", "luatools-button");
            pullBtn(".luatools-button", "luatools-restart-button");
          };
          if (window.__LuaToolsHiddenRowObserver) {
            try { window.__LuaToolsHiddenRowObserver.disconnect(); } catch (_) {}
          }
          window.__LuaToolsHiddenRowObserver = new MutationObserver(pillPull);
          window.__LuaToolsHiddenRowObserver.observe(hiddenRow, { childList: true });
        }
      }
"""

# The pill block of the CURRENT revision (everything after the shared anchor).
P1_NEW_TAIL = P1_NEW.replace(P1_OLD, "", 1)

# ── Patch 2: fix the button-class template lookup ─────────────────────────────
# Both buttons copy their CSS classes from the first <a> in the container
# ("look like the SteamDB/PCGW buttons"). Steam fills that row asynchronously,
# so on a slow load our Restart button can be the ONLY <a> in it - then the
# LuaTools button is constructed with the Restart button's classes and wrongly
# carries .luatools-restart-button forever (it is built before the backend
# presence check resolves, so the relocation repair in patch 1 never sees it
# being moved). Exclude our own buttons from the template lookup so an
# otherwise-empty row yields the default classes instead.
P2_OLD = ': steamdbContainer.querySelector("a");'
P2_NEW = ': steamdbContainer.querySelector("a:not(.luatools-restart-button):not(.luatools-button)");'
P2_EXPECTED = 2  # one for the Restart button, one for the LuaTools button

# Patch 3 replaces the external icon-font loader with self-contained SVGs.
# Keep the existing <i> elements, styles, animation, and event targets intact.
P3_OLD = """  function ensureFontAwesome() {
    if (document.getElementById("luatools-fontawesome")) return;
    try {
      const link = document.createElement("link");
      link.id = "luatools-fontawesome";
      link.rel = "stylesheet";
      link.href =
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css";
      link.integrity =
        "sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==";
      link.crossOrigin = "anonymous";
      link.referrerPolicy = "no-referrer";
      document.head.appendChild(link);
    } catch (err) {
      backendLog("LuaTools: Font Awesome injection failed: " + err);
    }
  }"""
P3_NEW = r"""  function ensureFontAwesome() {
    // [FLUENTY-PATCH-3] self-contained SVG icons, no remote font required
    if (window.__LuaToolsFluentySvgIcons) {
      window.__LuaToolsFluentySvgIcons.scan();
      return;
    }
    const drawings = {
      "fa-discord": '<path d="M8 5 7 3 3 5C1 9 1 14 2 17l5 2 1-2m8-12 1-2 4 2c2 4 2 9 1 12l-5 2-1-2M7 16c3 2 7 2 10 0M8 11v2m8-2v2M7 5c3-1 7-1 10 0"/>',
      "fa-gear": '<path d="m10 3-.5 3-2 1-3-.8-2 3 2.2 2v2L2.5 15l2 3 3-.8 2 1 .5 3h4l.5-3 2-1 3 .8 2-3-2.2-1.8v-2l2.2-2-2-3-3 .8-2-1L14 3Z"/><circle cx="12" cy="12" r="3"/>',
      "fa-xmark": '<path d="m6 6 12 12M18 6 6 18"/>',
      "fa-cloud-arrow-down": '<path d="M7 17H6a4 4 0 0 1-.8-7.9A7 7 0 0 1 18.8 8a4.5 4.5 0 0 1-.3 9H17M12 12v10m-4-4 4 4 4-4"/>',
      "fa-wrench": '<path d="M14 6a5 5 0 0 0-6 6L2 18a2.8 2.8 0 0 0 4 4l6-6a5 5 0 0 0 6-6l-4 3-3-3Z" transform="translate(1 -1)"/>',
      "fa-trash-can": '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
      "fa-spinner": '<path d="M21 12a9 9 0 1 1-9-9"/>',
      "fa-lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
      "fa-circle-info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
      "fa-info-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
      "fa-circle-question": '<circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 5m0 3v.1"/>',
      "fa-circle-check": '<circle cx="12" cy="12" r="9"/><path d="m7 12 3 3 7-7"/>',
      "fa-circle-xmark": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>'
    };
    const style = document.createElement("style");
    style.id = "luatools-fluenty-svg-icons";
    style.textContent =
      '[data-luatools-svg-icon]{display:inline-flex!important;align-items:center;' +
      'justify-content:center;vertical-align:-.125em;font-style:normal!important;line-height:1!important;}' +
      '[data-luatools-svg-icon]::before,[data-luatools-svg-icon]::after{content:none!important;display:none!important;}' +
      '[data-luatools-svg-icon]>svg{display:block!important;width:1em!important;height:1em!important;' +
      'flex:none;overflow:visible;fill:none!important;stroke:currentColor!important;' +
      'stroke-width:1.8!important;stroke-linecap:round;stroke-linejoin:round;pointer-events:none;}';
    (document.head || document.documentElement).appendChild(style);
    function scan() {
      document.querySelectorAll("i.fa-solid, i.fa-brands").forEach(function (el) {
        // Never replace Steam/theme/other plugins' icons.
        if (!el.closest('[class*="luatools-"]')) return;
        const name = Object.keys(drawings).find(function (key) {
          return el.classList.contains(key);
        });
        if (!name) return;
        if (el.getAttribute("data-luatools-svg-icon") === name &&
            el.querySelector("svg")) return;
        el.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" ' +
          'aria-hidden="true" focusable="false">' + drawings[name] + '</svg>';
        el.setAttribute("data-luatools-svg-icon", name);
      });
    }
    let pending = false;
    const observer = new MutationObserver(function () {
      if (pending) return;
      pending = true;
      Promise.resolve().then(function () { pending = false; scan(); });
    });
    window.__LuaToolsFluentySvgIcons = { scan: scan, observer: observer };
    observer.observe(document.documentElement, {
      childList: true, subtree: true, attributes: true, attributeFilter: ["class"]
    });
    scan();
  }"""


def write_out(patched):
    out = patched.replace("\n", "\r\n") if crlf_mode else patched
    try:
        with open(TARGET, "wb") as f:
            f.write(out.encode("utf-8"))
    except PermissionError:
        print("[!] Permission denied writing the file. Close the LuaTools app and/or run as Administrator.")
        return False
    return True


def print_done():
    print("\n[DONE] For the patch to take effect:")
    print("    1. Exit LuaTools from the system tray and start it again")
    print("       (it loads luatools.js into memory at startup).")
    print("    2. Refresh or reopen the Steam store pages.")
    print("    Note: a Steam restart is NOT required.")
    print("    Heads-up: LuaTools re-downloads this file when the plugin updates,")
    print("    which reverts this patch - just re-run this script afterwards.")


def main():
    patched = normalized_content
    actions = []  # (description, old, new, expected_count)

    # ── Validate patch 1 (pill split placement) ──
    if P1_SENTINEL in patched:
        if patched.count(P1_NEW_TAIL) == 1:
            print("[=] Patch 1 already applied (current revision).")
        elif patched.count(P1_OLD_TAIL) == 1:
            actions.append(("upgrade patch 1 to the current revision (button relocation +"
                            "\n    role-class repair + hidden reference anchor)",
                            P1_OLD_TAIL, P1_NEW_TAIL, 1))
        else:
            print("[!] The file contains an older Fluenty patch, but its block was")
            print("    not recognized exactly. Restore the .bak backup (or let LuaTools")
            print("    re-download the frontend) and run this script again.")
            print("    No changes were made.")
            return 1
    else:
        anchor_count = patched.count(P1_OLD)
        if anchor_count == 0:
            print("[!] Could not find the expected code block in the target file.")
            print("    This LuaTools frontend version may be unsupported. No changes were made.")
            return 1
        if anchor_count > 1:
            print(f"[!] Found {anchor_count} copies of the expected code block (expected exactly 1).")
            print("    Refusing to patch an ambiguous file. No changes were made.")
            return 1
        actions.append(("patch 1 (split placement)", P1_OLD, P1_NEW, 1))

    # ── Validate patch 2 (button-class template fix) ──
    if patched.count(P2_NEW) == P2_EXPECTED:
        print("[=] Patch 2 already applied.")
    else:
        anchor_count = patched.count(P2_OLD)
        if anchor_count == 0:
            print("[!] Could not find the button-template lookup code (patch 2).")
            print("    This LuaTools frontend version may be unsupported. No changes were made.")
            return 1
        if anchor_count != P2_EXPECTED:
            print(f"[!] Found {anchor_count} copies of the button-template lookup (expected exactly {P2_EXPECTED}).")
            print("    Refusing to patch an ambiguous file. No changes were made.")
            return 1
        actions.append(("patch 2 (own buttons excluded as class templates)", P2_OLD, P2_NEW, P2_EXPECTED))

    # Validate the entire icon-loader block before touching the file.
    if patched.count(P3_NEW) == 1 and patched.count(P3_OLD) == 0:
        print("[=] Patch 3 already applied (embedded SVG icons).")
    elif patched.count(P3_OLD) == 1 and "[FLUENTY-PATCH-3]" not in patched:
        actions.append(("patch 3 (embedded SVG icons, no remote font)", P3_OLD, P3_NEW, 1))
    else:
        print("[!] Icon-loader code is unsupported or ambiguous (patch 3).")
        print("    No changes were made.")
        return 1

    if not actions:
        print("\n[=] Everything already applied. Nothing to do.")
        return 0

    # All anchors validated - only now back up and write.
    if not os.path.exists(BACKUP):
        shutil.copy2(TARGET, BACKUP)
        print(f"[+] Backup created: {BACKUP}")
    else:
        print(f"[=] Backup already exists: {BACKUP}")

    for description, old, new, expected in actions:
        assert patched.count(old) == expected
        patched = patched.replace(old, new, expected)
        print(f"[+] Applied {description}.")

    if not write_out(patched):
        return 1
    print_done()
    return 0


if __name__ == "__main__":
    code = main()
    try:
        input("\nPress Enter to exit...")
    except EOFError:
        pass
    sys.exit(code)
