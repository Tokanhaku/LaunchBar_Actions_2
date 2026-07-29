//
// Font Awesome 7 Icons
// LaunchBar Action – default.js
//
// Browses the icons of the current Font Awesome Free release. The glyphs are
// drawn straight from the installed OTFs via LaunchBar's `character:?font=`
// icon syntax, so no icon images have to be rendered or bundled.
//

include('faindex.js');

var FONT_DIR = LaunchBar.homeDirectory + '/Library/Fonts';
var RELEASE_API = 'https://api.github.com/repos/FortAwesome/Font-Awesome/releases/latest';

function repoURL(version, path) {
    return 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/' + version + '/' + path;
}

// The updater writes to the action's support directory so that the bundle
// itself stays untouched; whatever is there wins over the shipped index.
function indexPath() {
    var updated = Action.supportPath + '/icons.json';
    return File.exists(updated) ? updated : Action.path + '/Contents/Resources/icons.json';
}

function loadIndex() {
    return File.readJSON(indexPath());
}

function fontsInstalled(index) {
    var files = fontFilesForVersion(index.version);
    return Object.keys(files).every(function (style) {
        return File.exists(FONT_DIR + '/' + files[style]);
    });
}


// ---------------------------------------------------------------- items

function iconString(character, font) {
    return 'character:' + character + '?font=' + encodeURIComponent(font);
}

function websiteURL(entry, style) {
    var family = style === 'brands' ? 'brands' : 'classic';
    return 'https://fontawesome.com/icons/' + (entry.of || entry.n) +
        '?f=' + family + '&s=' + (style === 'brands' ? 'regular' : style);
}

function makeItem(entry, style, index) {
    var font = index.fonts[style];
    var character = String.fromCodePoint(parseInt(entry.u, 16));
    var classes = 'fa-' + style + ' fa-' + entry.n;
    var unicode = 'U+' + entry.u.toUpperCase();

    var subtitle = capitalize(style) + '  ·  ' + unicode;
    if (entry.of) subtitle = 'Alias of ' + entry.of + '  ·  ' + subtitle;
    else if (entry.l && entry.l.toLowerCase() !== entry.n) subtitle = entry.l + '  ·  ' + subtitle;

    return {
        title: entry.n,
        subtitle: subtitle,
        alwaysShowsSubtitle: true,
        // Both spellings of the same thing – whichever one LaunchBar reads,
        // the glyph is drawn with the Font Awesome face.
        icon: iconString(character, font),
        iconFont: font,
        action: 'useIcon',
        actionArgument: {
            name: entry.n,
            style: style,
            character: character,
            font: font,
            classes: classes,
            unicode: unicode,
            url: websiteURL(entry, style),
        },
        infoItems: [
            { label: 'CSS Classes', title: classes },
            { label: 'HTML', title: '<i class="' + classes + '"></i>' },
            { label: 'Unicode', title: unicode },
            { label: 'LaunchBar Icon', title: iconString(character, font) },
            { label: 'Glyph', title: character, icon: iconString(character, font), iconFont: font },
            {
                title: 'Look Up on fontawesome.com',
                url: websiteURL(entry, style),
                icon: iconString(character, font),
                iconFont: font,
            },
        ],
    };
}

function capitalize(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
}


// ---------------------------------------------------------------- search

// Only used when a string is passed to the action (hit Space, then type).
// Plain browsing relies on LaunchBar's own filtering of the returned list,
// which matches titles only – this one also looks at Font Awesome's own
// search terms, so "notification" finds the bell and flag icons.
function score(entry, query) {
    var name = entry.n;
    if (name === query) return 0;
    if (name.indexOf(query) === 0) return 1;
    if (name.indexOf(query) !== -1) return 2;
    if (entry.l.toLowerCase().indexOf(query) !== -1) return 3;

    var best = -1;
    entry.t.forEach(function (term) {
        term = term.toLowerCase();
        if (term === query) best = best === -1 ? 4 : Math.min(best, 4);
        else if (term.indexOf(query) === 0) best = best === -1 ? 5 : Math.min(best, 5);
        else if (term.indexOf(query) !== -1) best = best === -1 ? 6 : Math.min(best, 6);
    });
    return best;
}

function search(entries, argument, mode) {
    var queries = argument.toLowerCase().split(/\s+/).filter(Boolean);
    var hits = [];

    entries.forEach(function (entry) {
        // Skip what the current style mode would drop anyway, so hidden icons
        // don't eat into the result limit below.
        if (stylesFor(entry, mode).length === 0) return;

        var total = 0;
        for (var i = 0; i < queries.length; i++) {
            var s = score(entry, queries[i]);
            if (s === -1) return;
            total += s;
        }
        hits.push({ entry: entry, score: total });
    });

    // Equal relevance: prefer the shorter name, so "notification" surfaces
    // "bell" ahead of "anchor-circle-exclamation".
    hits.sort(function (a, b) {
        if (a.score !== b.score) return a.score - b.score;
        if (a.entry.n.length !== b.entry.n.length) return a.entry.n.length - b.entry.n.length;
        return a.entry.n < b.entry.n ? -1 : a.entry.n > b.entry.n ? 1 : 0;
    });

    return hits.slice(0, 200).map(function (hit) { return hit.entry; });
}


// ---------------------------------------------------------------- styles

// Font Awesome Free is lopsided: nearly every icon exists in solid, but only
// a small minority also comes in regular. Which of the two an icon is shown
// in is therefore a preference rather than a fixed rule. Brands is not an
// alternative weight – a brand mark exists in that style only – so it is
// always kept.
var STYLE_MODES = [
    {
        id: 'regular',
        title: 'Regular only',
        detail: 'Outline icons and brands. Icons that Font Awesome Free only draws in solid are hidden.',
    },
    {
        id: 'prefer-regular',
        title: 'Prefer regular',
        detail: 'One row per icon: regular where it exists, solid otherwise.',
    },
    {
        id: 'all',
        title: 'All styles',
        detail: 'Every icon in every style it is available in.',
    },
];

function currentMode() {
    var mode = Action.preferences.styleMode;
    var known = STYLE_MODES.some(function (m) { return m.id === mode; });
    return known ? mode : 'regular';
}

function stylesFor(entry, mode) {
    if (mode === 'all') return entry.s;

    var keep = [];
    if (entry.s.indexOf('brands') !== -1) keep.push('brands');
    if (entry.s.indexOf('regular') !== -1) keep.push('regular');
    else if (mode === 'prefer-regular' && entry.s.indexOf('solid') !== -1) keep.push('solid');
    return keep;
}


// ---------------------------------------------------------------- run

function run(argument) {
    var index = loadIndex();

    if (!fontsInstalled(index)) {
        return [{
            title: 'Install Font Awesome ' + index.version + ' Fonts',
            subtitle: 'Downloads the OTFs into ~/Library/Fonts – required to display the icons',
            alwaysShowsSubtitle: true,
            icon: 'symbol:arrow.down.circle',
            action: 'installFonts',
            actionArgument: index.version,
            actionRunsInBackground: true,
        }];
    }

    var mode = currentMode();
    var searching = argument !== undefined && argument.trim() !== '';
    var entries = searching ? search(index.icons, argument.trim(), mode) : index.icons;

    var items = [];
    entries.forEach(function (entry) {
        stylesFor(entry, mode).forEach(function (style) {
            items.push(makeItem(entry, style, index));
        });
    });

    if (!searching) {
        items.push(styleModeItem(mode, items.length));
        items.push({
            title: 'Font Awesome ' + index.version,
            subtitle: 'Open to check for a newer release',
            alwaysShowsSubtitle: true,
            icon: 'symbol:arrow.triangle.2.circlepath',
            action: 'checkForUpdate',
            actionArgument: index.version,
            actionRunsInBackground: true,
        });
    }

    return items;
}

function styleModeItem(mode, shown) {
    var active = STYLE_MODES.filter(function (m) { return m.id === mode; })[0];

    return {
        title: 'Style: ' + active.title,
        subtitle: shown + ' icons shown  ·  Open to change',
        alwaysShowsSubtitle: true,
        icon: 'symbol:slider.horizontal.3',
        children: STYLE_MODES.map(function (m) {
            return {
                title: m.title,
                subtitle: m.detail,
                alwaysShowsSubtitle: true,
                icon: m.id === mode ? 'symbol:checkmark.circle.fill' : 'symbol:circle',
                action: 'setStyleMode',
                actionArgument: m.id,
                actionReturnsItems: true,
            };
        }),
    };
}

function setStyleMode(mode) {
    Action.preferences.styleMode = mode;
    return run();
}


// ---------------------------------------------------------------- actions

// Enter copies the CSS classes; modifiers copy the other representations.
function useIcon(icon) {
    if (LaunchBar.options.shiftKey) {
        LaunchBar.openURL(icon.url);
        return;
    }

    var value, what;
    if (LaunchBar.options.commandKey) {
        value = iconString(icon.character, icon.font);
        what = 'LaunchBar icon string';
    } else if (LaunchBar.options.alternateKey) {
        value = icon.character;
        what = 'glyph';
    } else if (LaunchBar.options.controlKey) {
        value = '<i class="' + icon.classes + '"></i>';
        what = 'HTML';
    } else {
        value = icon.classes;
        what = 'CSS classes';
    }

    LaunchBar.setClipboardString(value);
    LaunchBar.displayNotification({
        title: 'fa-' + icon.name,
        string: 'Copied ' + what + ': ' + value,
    });
    LaunchBar.hide();
}

function installFonts(version) {
    var files = fontFilesForVersion(version);

    if (!File.exists(FONT_DIR)) File.createDirectory(FONT_DIR);

    try {
        Object.keys(files).forEach(function (style) {
            var file = files[style];
            LaunchBar.execute('/usr/bin/curl', '-fsSL',
                '-o', FONT_DIR + '/' + file,
                repoURL(version, 'otfs/' + encodeURIComponent(file)));
        });
    } catch (exception) {
        LaunchBar.alert('Could not install the fonts', String(exception));
        return false;
    }

    LaunchBar.displayNotification({
        title: 'Font Awesome ' + version,
        string: 'Fonts installed in ~/Library/Fonts.',
    });
    return true;
}

function checkForUpdate(currentVersion) {
    var response = HTTP.getJSON(RELEASE_API);
    if (response.error || !response.data || !response.data.tag_name) {
        LaunchBar.alert('Could not check for updates',
            response.error || 'Unexpected response from the GitHub API.');
        return;
    }

    var latest = response.data.tag_name.replace(/^v/, '');
    if (latest === currentVersion) {
        LaunchBar.displayNotification({
            title: 'Font Awesome ' + currentVersion,
            string: 'This is the latest release.',
        });
        return;
    }

    if (LaunchBar.alert('Font Awesome ' + latest + ' is available',
        'You have ' + currentVersion + '. Updating downloads the new fonts into ' +
        '~/Library/Fonts and rebuilds this action’s icon index.',
        'Update', 'Cancel') !== 0) {
        return;
    }

    var metadata = HTTP.getJSON(repoURL(latest, 'metadata/icons.json'));
    if (metadata.error || !metadata.data) {
        LaunchBar.alert('Could not download the icon metadata',
            metadata.error || 'Unexpected response for version ' + latest + '.');
        return;
    }

    if (!installFonts(latest)) return;
    File.writeJSON(buildIndex(metadata.data, latest), Action.supportPath + '/icons.json');

    LaunchBar.displayNotification({
        title: 'Updated to Font Awesome ' + latest,
        string: 'Run the action again to browse the new icons.',
    });
}
