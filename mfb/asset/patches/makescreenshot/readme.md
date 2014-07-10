**Goal:**
bge.render.makeScreenshot(file) is extended to accept dimension information in the form of makeScreenshot(file, xOrigin, yOrigin, width, height)

**Status:**

- Fully backward compatible.
- Works fine on blenderplayer
- Does not work on Blender since canvas is treated differently.
(is the trunk one working on Blender?)