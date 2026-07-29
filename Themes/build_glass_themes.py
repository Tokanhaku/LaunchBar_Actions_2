#!/usr/bin/env python3
"""Generate the 'Glass' LaunchBar themes (light + dark) into the user Themes folder."""

import os
import plistlib
import shutil

THEMES_DIR = os.path.expanduser("~/Library/Application Support/LaunchBar/Themes")
PREFIX = "com.tokanhaku.LaunchBar.theme."

# --- shared look -------------------------------------------------------------

def light_props(material, tint, parent="at.obdev.LaunchBar.theme.Default"):
    return {
        "parent": parent,

        # --- window: the glass slab ---
        "windowBackgroundMaterial": str(material),
        "windowBackgroundColor": tint,             # thin white tint over the blur
        # NB: the alpha here is the only see-through knob a theme has — there is no
        # windowBackgroundAlphaValue / windowBackgroundBlurRadius theme key.
        "windowCornerRadius": 28,
        "windowCornerShapeExponent": 3.5,          # continuous / squircle corners
        "windowShadowStyle": 3,
        # On a bright backdrop a white rim just reads as haze, and a blurred inner
        # highlight smears the edge — so light mode gets one dark 1px hairline
        # (0.5pt on Retina) and no inner shadow at all. Dark mode is the opposite,
        # see dark_props.
        "windowHasBorder": True,
        "windowBorderColor": "#00000040",
        "windowBorderWidth": 0.5,
        "windowBorderInset": 0.25,
        "windowHasInnerShadow": False,

        # --- input area: subtle top sheen ---
        "inputAreaBackgroundGradient": {"0.0": "#FFFFFF14", "1.0": "#FFFFFF00"},
        # The typed abbreviation sits right on the see-through backdrop at 5% tint.
        # Default leaves it at the 50%-black dimmed colour AND sets
        # inputAreaTextShadowColor to clearColor, so the halo other text gets never
        # reaches it — hence its own colour plus its own halo here.
        "inputAreaAbbreviationTextColor": "0 0 0 0.82",
        "inputAreaTextShadowColor": "1 1 1 0.7",
        "inputAreaTextShadowBlurRadius": 1.0,

        # --- item list: no grid lines, floating capsule selection ---
        "itemListEdgeInsets": "8 8 8 8",
        "itemListGridLineGradient": {"0.0": "#00000000", "1.0": "#00000000"},
        "itemListGridLineShadowHeight": 0,
        "itemListSeparatorUpperLineColor": "#00000012",
        "itemListSeparatorLowerLineColor": "#FFFFFF33",
        "itemListSeparatorLowerLineThickness": 1,
        "itemListSelectionHighlightColor": "0.16 0.56 1 0.7",
        "itemListSelectionCornerRadius": 22,
        "itemListSelectionCornerShapeExponent": 4,
        "itemListScrollerColor": "#00000030",
        "itemListLabeledExtraDetailsBackgroundColor": "#0000001A",

        # icons pick up a soft light from above
        "templateIconShadowColor": "#FFFFFF66",
        "templateIconShadowOffset": "0 -1",
    }


def dark_props(parent, tint, material=None):
    props = {
        "parent": parent,

        "windowBackgroundIsDark": True,
        "windowBackgroundColor": tint,
        # Pinned, so whatever edge treatment a light variant tries, dark keeps the
        # one that was already dialled in.
        "windowHasBorder": True,
        "windowBorderColor": "#FFFFFF40",
        "windowBorderWidth": 1,
        "windowBorderInset": 0.5,
        "windowHasInnerShadow": True,
        "windowInnerShadowColor": "#FFFFFF33",
        "windowInnerShadowOffset": "0 -1.5",
        "windowInnerShadowBlurRadius": 3,

        "inputAreaBackgroundGradient": {"0.0": "#FFFFFF18", "1.0": "#FFFFFF05"},

        "defaultTextColor": "whiteColor",
        "defaultDimmedTextColor": "1 1 1 0.5",
        "defaultTextShadowColor": "#00000033",
        "defaultTextShadowColor@2x": "clearColor",
        "inputAreaTextColor": "@defaultTextColor",
        "inputAreaAbbreviationTextColor": "#f9f9f9",
        # light mode puts a white halo here; a white halo under white text would glow
        "inputAreaTextShadowColor": "clearColor",
        "inputAreaTextShadowBlurRadius": 0,
        "inputAreaActionMenuAreaBackgroundColor": "1 1 1 0.1",
        "inputAreaNonKeyWindowTextColorOffsetLevel": -0.3,

        "itemListSubtitleTextColor": "@defaultTextColor * 0.65",
        "itemListSeparatorUpperLineColor": "#FFFFFF12",
        "itemListSeparatorLowerLineColor": "#FFFFFF20",
        "itemListScrollerColor": "#FFFFFF60",
        "itemListLabeledExtraDetailsBackgroundColor": "#FFFFFF15",
        "itemListStagedItemHighlightLevel": 0.3,
        "itemListSelectionSubsearchHighlightColor": "0.85 0.5 0 1",
        "itemListNavigationArrowImage": "@itemListSelectedNavigationArrowImage",
        "textInputSelectedTextBackgroundColor": "@itemListSelectionHighlightColor - 0.3",

        "templateIconShadowColor": "#00000060",
    }
    # Materials 0-2 are the legacy appearance-*specific* ones: 1 (.light) stays
    # light even in dark mode, so a dark variant built on it must switch to 2.
    # The modern materials adapt on their own and need no override.
    if material is not None:
        props["windowBackgroundMaterial"] = str(material)
    return props


# NSVisualEffectMaterial 1/2 = legacy .light/.dark: the thinnest blur on Tahoe and
# therefore the most see-through. Every value here was picked by eye — see the
# theme section of CLAUDE.md before changing any of them.
MATERIAL, DARK_MATERIAL = 1, 2
TINT, DARK_TINT = "#FFFFFF0D", "#0000001A"

VARIANTS = [
    ("Glass", "Glass", {}),
]


def write_theme(dir_name, bundle_id, bundle_name, props):
    root = os.path.join(THEMES_DIR, dir_name + ".lbtheme")
    if os.path.exists(root):
        shutil.rmtree(root)
    res = os.path.join(root, "Contents", "Resources")
    os.makedirs(res)
    with open(os.path.join(root, "Contents", "Info.plist"), "wb") as f:
        plistlib.dump({"CFBundleIdentifier": bundle_id,
                       "CFBundleName": bundle_name}, f)
    with open(os.path.join(res, "Properties.plist"), "wb") as f:
        plistlib.dump(props, f)
    return root


os.makedirs(THEMES_DIR, exist_ok=True)
for stem, name, overrides in VARIANTS:
    light_id = PREFIX + stem
    props = light_props(MATERIAL, TINT)
    props.update(overrides)
    write_theme(stem, light_id, name, props)
    write_theme(stem + ".dark", light_id + ".dark", name + " Dark",
                dark_props(light_id, DARK_TINT, DARK_MATERIAL))
    print(f"{name:12} {light_id}\n             light overrides: {overrides or '-'}")
