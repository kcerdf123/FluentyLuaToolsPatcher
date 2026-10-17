# FluentyLuaToolsPatcher

A lightweight compatibility patch that resolves functional, layout, and visual conflicts between the **Steam Fluenty skin** and the **LuaTools** client modification. Built and verified for the latest releases of both the theme and plugin (and should continue to work after updates)! 

**Big shoutout to _Kristijan1001_ over at the Discord for giving me the idea to do this with the v2 plugin! Without his base patch, this wouldn't be possible.**

## Key Features

* **Restores Injected UI Elements:** Fixes missing buttons, script menus, and the *Add Game* action hidden by default skin overrides.
* **Layout & Alignment Correction:** Resolves overlapping text containers, misaligned toolbars, and broken margins across client views.
* **Fluent Design Integration:** Re-styles LuaTools interface components to match the modern aesthetics of the Fluenty theme seamlessly.
* **Stable Script Hooks:** Ensures core Lua execution triggers and interface callbacks persist properly after client updates.

## Installation

1. Run the patcher script (LuaTools Fluenty Theme Patch.py script file). Make sure you have the regular version of Python (from here: https://www.python.org/downloads/) installed or this will **not** work!
2. The patcher will attempt to locate your LuaTools directory automatically.
3. If automatic detection fails, enter the full path to your `luatools.js` file when prompted (located inside your LuaTools installation folder).
4. Restart Steam AND LuaTools to apply the changes.
