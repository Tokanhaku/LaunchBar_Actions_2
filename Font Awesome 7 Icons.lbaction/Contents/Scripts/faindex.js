//
// faindex.js
//
// Shared code: turns Font Awesome's official `metadata/icons.json` into the
// compact index this action browses. Used both by default.js (at build time
// the result is shipped in Resources/icons.json) and by the in-action updater,
// so there is only one place that knows the metadata layout.
//

// Font Awesome ships one OTF per style, and the names carry the major version,
// so they can be derived from the release.
//
// These must be the display names, not the PostScript names: LaunchBar resolves
// an icon font by family, and a family lookup for "FontAwesome7Free-Solid"
// returns nothing – the icons then fall back to the system font and render as
// the LastResort “?” glyph. Note that "Font Awesome 7 Free Regular" fails that
// same lookup, so the regular style has to go through the bare family name,
// whose regular face it is.
function fontNamesForVersion(version) {
    var major = String(version).split('.')[0];
    return {
        solid: 'Font Awesome ' + major + ' Free Solid',
        regular: 'Font Awesome ' + major + ' Free',
        brands: 'Font Awesome ' + major + ' Brands',
    };
}

// File names of the OTFs inside the release, same naming scheme.
function fontFilesForVersion(version) {
    var major = String(version).split('.')[0];
    return {
        solid: 'Font Awesome ' + major + ' Free-Solid-900.otf',
        regular: 'Font Awesome ' + major + ' Free-Regular-400.otf',
        brands: 'Font Awesome ' + major + ' Brands-Regular-400.otf',
    };
}

var STYLE_ORDER = ['solid', 'regular', 'brands'];

// icons: the parsed metadata/icons.json of a Font Awesome release.
// Only icons included in Font Awesome Free are kept – the fonts we install
// cannot render Pro-only styles anyway.
function buildIndex(icons, version) {
    var entries = [];

    Object.keys(icons).forEach(function (name) {
        var meta = icons[name];
        var styles = STYLE_ORDER.filter(function (style) {
            return (meta.free || []).indexOf(style) !== -1;
        });
        if (styles.length === 0) return;

        var base = {
            l: meta.label || name,
            u: meta.unicode,
            s: styles,
            t: (meta.search && meta.search.terms) || [],
        };

        entries.push(Object.assign({ n: name }, base));

        // Old names (fa-remove, fa-close, …) stay searchable as their own
        // entries, pointing back at the icon they were renamed to.
        var aliases = (meta.aliases && meta.aliases.names) || [];
        aliases.forEach(function (alias) {
            entries.push(Object.assign({ n: alias, of: name }, base));
        });
    });

    entries.sort(function (a, b) {
        return a.n < b.n ? -1 : a.n > b.n ? 1 : 0;
    });

    return {
        version: version,
        fonts: fontNamesForVersion(version),
        icons: entries,
    };
}
