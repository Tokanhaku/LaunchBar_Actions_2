# LaunchBar Actions 开发笔记

这个目录是 LaunchBar 的用户 action 目录（`~/Library/Application Support/LaunchBar/Actions`），同时是个 git repo。
下面是实际踩过坑总结出来的东西，动手前先看一遍，能省掉大量试错。

当前环境：LaunchBar 6.24 / macOS 15 (Darwin 25) / Apple Silicon。

---

## 1. 官方文档怎么读

`https://developer.obdev.at/launchbar-developer-documentation/` 是个 SPA，直接 curl 首页拿不到内容。
真正的页面在 **`topics/<anchor>.html`**，anchor 从 `toc.json` 里取：

```sh
curl -s "https://developer.obdev.at/launchbar-developer-documentation/toc.json"
curl -s "https://developer.obdev.at/launchbar-developer-documentation/topics/script-output.html"
```

常用页面：`action-info-plist`（Info.plist 全部 key + 图标字符串语法）、`script-output`（返回项的全部属性）、
`javascript-launchbar` / `javascript-file` / `javascript-action` / `javascript-http` / `javascript-global-functions`。

---

## 2. 图标系统（最容易踩坑的地方）

`CFBundleIconFile` 和返回项的 `icon` 用同一套语法：

| 形式 | 例子 | 说明 |
|---|---|---|
| bundle 内图片名 | `MyIconTemplate.pdf` | 找 action 的 Resources，再找 LaunchBar 的 |
| SF Symbol | `symbol:waveform.circle` | 系统自带，**零依赖，分享首选** |
| 应用 bundle id | `com.apple.Mail` | 用那个 app 的图标 |
| 任意字符 | `character:X?font=Futura%20Medium` | 用指定字体渲染字形 |
| LaunchBar 自带 FA | `font-awesome:fa-flag` | Font Awesome **4.7**，2016 年的老版本 |
| emoji / 绝对路径 / data URI | | |

**命名以 `Template` 结尾的图片会被当 template image**（只取 alpha，自动适配深浅色和选中态）。
`character:` 和 `font-awesome:` 的图标**永远是 template**，emoji 永远不是。

### 坑 1：字体名必须用 display name，不能用 PostScript name

LaunchBar 内部是 `characterImageWithSize:fontName:bordered:`，**按字族解析**。
family 查找对 PostScript 名返回 nil → 回退系统字体 → 私用区码位（U+E000–F8FF）→ LastResort 字体 → **画出一个问号**。
失败是静默的，只能靠肉眼发现。

```
                              NSFont(name:)   family 查找
FontAwesome7Free-Solid            ✓              ✗ nil     ← 会变问号
Font Awesome 7 Free Solid         ✓              ✓         ← 正确
Font Awesome 7 Free Regular       ✓              ✗ nil     ← 也会变问号！
Font Awesome 7 Free               ✓ (→Regular)   ✓         ← regular 必须用裸字族名
```

**动手前一定要用 Swift 实测两种查找方式**，别猜：

```swift
NSFont(name: n, size: 32)
NSFontManager.shared.font(withFamily: n, traits: [], weight: 5, size: 32)
```

保险做法是 `icon` 里写 `character:X?font=<encodeURIComponent(name)>` 的同时也给 `iconFont` 属性，两种写法都给上。

### 坑 2：action 无法自带图标字体（影响分享）

`CFBundleIconFile` 在**任何脚本运行之前**就被解析。所以：

- 字体放进 `Contents/Resources` 没用 —— macOS 不自动注册 bundle 内字体
- 脚本里 `CTFontManagerRegisterFontsForURL` 也没用 —— JS 没这个 API，且图标早解析完了

**结论：要分享的 action 只能用 `symbol:` / bundle 内的 Template PDF·PNG / `font-awesome:`（LaunchBar 自带字体，任何用户都有）。
只在自己机器上跑的 action 才可以依赖 `~/Library/Fonts` 里装的第三方字体。**

---

## 3. JavaScript API 要点

- `include('shared.js')` —— 路径相对 `Contents/Scripts/`，可以多个脚本共享代码
- `Action.path` / `Action.supportPath` / `Action.cachePath` / `Action.preferences`
  - `preferences` 是个对象，脚本结束时自动写回 `Preferences.plist`，做设置项很方便
  - 运行时要生成的数据写 `supportPath`，别污染 bundle；读的时候 supportPath 优先、fallback 回 Resources
- `LaunchBar.options.{commandKey,alternateKey,shiftKey,controlKey}` —— 修饰键，用来给一个条目挂多种行为
- `LaunchBar.alert(msg, info, btn1, btn2)` —— **返回值最右边的按钮是 0**，往左递增。`btn1` 是默认按钮（最右）
- `LaunchBar.execute('/usr/bin/curl', '-fsSL', '-o', dst, url)` —— 比 `executeAppleScript` + `do shell script` 干净，没有转义地狱
- `HTTP.getJSON(url)` 返回 `{data}` 或 `{error}`；几 MB 的 JSON 也扛得住
- `File.readJSON/writeJSON/readText/writeText/exists/createDirectory`（注意 `writeText(text, path)` 是内容在前）

### 返回项属性

`title` / `subtitle` / `alwaysShowsSubtitle` / `label` / `badge` / `icon` / `iconFont` / `iconIsTemplate` /
`url` / `path` / `quickLookURL` / `action` / `actionArgument`（可以是对象）/ `actionReturnsItems` /
`actionRunsInBackground` / `actionBundleIdentifier` / `children` / `infoItems`

**没有搜索关键词字段** —— LaunchBar 的列表内过滤只匹配 `title`。要按别名/标签搜，得自己实现：
`LBAcceptedArgumentTypes: ["string"]` + `LBLiveFeedbackEnabled` + `LBRequiresArgument: false`，
用户按空格进入文本输入，`run(argument)` 逐键收到输入，自己打分排序。

### Info.plist 常用 key

`LBScripts.LBDefaultScript` 里：`LBScriptName` / `LBReturnsResult` / `LBKeepWindowActive` /
`LBRequiresArgument` / `LBAcceptedArgumentTypes` / `LBLiveFeedbackEnabled` / `LBRunInBackground`。
顶层还有 `LBTextInputTitle` / `LBDescription`（`LBSummary`/`LBArgument`/`LBResult`/`LBRequirements` 会显示在信息面板）。

---

## 4. 怎么验证（这台机器上的实际限制）

**`screencapture` 被系统权限挡住，我看不到 LaunchBar 的实际渲染。** 视觉效果只能让用户确认。
但下面这些能自己验证：

1. **node harness** —— 把 `include`/`File`/`Action`/`LaunchBar`/`HTTP` 打桩，`eval` 脚本后直接调 `run()`。
   能验证全部逻辑、条目数量、搜索排序。
2. **确认 LaunchBar 真的能跑起来** —— 临时加个 `LBActionURLScript` 指向同一个脚本，写个
   `runWithURL()` 把结果写到文件，然后 `open "x-launchbar:action/<bundleId>"`，读那个文件。
   （`x-launchbar:action?name=...` 这种形式不存在；正确格式是 `x-launchbar:action/<bundleId>/path?query`，
   而且必须 action 显式声明了 `LBActionURLScript` 才会触发。）验证完记得删掉。
3. **字形覆盖** —— 用 Swift + CoreText 遍历索引，`CTFontGetGlyphsForCharacters` + `CTFontCreatePathForGlyph`
   检查每个码位是不是真有轮廓。测第三方字体可以用 `CTFontManagerRegisterFontsForURL(url, .process, &err)`
   只在进程内注册，不动系统。
4. `LaunchBar.log()` **不进 unified log**，`log show --predicate 'process == "LaunchBar"'` 什么都查不到，别浪费时间。

**改 Info.plist 需要重启 LaunchBar**（`osascript -e 'tell application "LaunchBar" to quit'` 后 `open -a LaunchBar`），
新建 action 也要重启才会被索引；**只改脚本不用重启**，每次运行都是重新读文件。

---

## 5. 本目录的约定

- bundle id：`com.tokanhaku.LaunchBar.action.<ActionName>`
- `LBDescription`：`LBAuthor` = Huanbo Tu，`LBEmail` = huanbo.tu@outlook.de，`LBTwitter` = @tokanhaku
- 图标现状：7 个用 `symbol:`，6 个用手工做的 `*-Template.png`（obsidian / claude / deepl / gemini / feather）

---

## 6. Font Awesome 7 Icons.lbaction

自己写的 action，用来替代 LaunchBar 内置的 "Font Awesome Icons"（那个读的是 app 内的 FA 4.7，786 个图标，
改不了 —— 动 app bundle 会破坏签名且每次升级被覆盖）。

- 字体：FA 7.3.1 Free 三个 OTF 装在 `~/Library/Fonts`
- 索引：`Contents/Resources/icons.json`（504 KB，2606 条 = 1992 个图标 + 614 个旧名 alias，2883 个图标/样式组合）
- `Contents/Scripts/faindex.js` 是共享的索引构建代码，**同一份代码**既用于 node 预生成，也用于 action 内的自更新
- 样式模式存在 `Action.preferences.styleMode`：`regular`(882) / `prefer-regular`(2610) / `all`(2883)，默认 regular
- 自更新：查 GitHub releases → 拉 `metadata/icons.json` → 重建索引写进 supportPath + curl 三个 OTF
- 字体名和文件名都按主版本号推导（`Font Awesome <major> Free Solid` / `Font Awesome <major> Free-Solid-900.otf`），FA 8 出了也能用

**已知问题（用户决定保持现状，不要再改）**：它自己的 `CFBundleIconFile` 依赖已安装的字体，
所以这个 action 分享给别人、对方没装字体的话，图标是问号。见第 2 节坑 2。

### FA 元数据的坑

- `metadata/icons.json` 里 `free` 字段才是免费可用的样式；`styles` 不可靠
- Free 包里的元数据是**裁剪过的** —— `icon-families.json` 的 `familyStylesByLicense.pro` 跟 free 一模一样，
  **推不出 Pro 有哪些 family/style**。要支持 Pro 必须拿到真实的 Pro desktop 包（授权内容，不要自己去找）
- alias 在 `aliases.names`，共 614 个，能覆盖 FA4/5 的旧名（`fa-remove` → `xmark`）
- Duotone 是两层字形叠加，`character:` 只画一层，用不了

---

## 7. 其他图标源的调研结论

**SF Symbols** —— `symbol:` 前缀，系统自带约 6900 个，多字重，零依赖。**通用概念图标的默认选择。**

**Lucide**（1.27.0，ISC 协议，全免费）—— 官方发字体：GitHub release 资产 `lucide-font-<ver>.zip` 里有 `lucide.ttf`
和 `codepoints.json`（扁平的 name→码位映射，2027 条，U+E038–E729）。
字体 PostScript / family / display 名**全是 `lucide`**，单字体单字重，两种查找方式都能解析，不会有第 2 节的坑。
**2027 个码位里 20 个是空字形**，正好是被废弃的品牌 logo（github/gitlab/facebook/twitter/youtube/slack/figma/
chrome/chromium/linkedin/dribbble/trello/instagram/twitch/codepen/codesandbox/framer/pocket + circle-euro-sign/rail-symbol），
建索引时必须过滤掉。tags/categories 不在字体包里，在主仓库的 `icons/*.json`。

**取舍**：要统一 outline 风格 → Lucide（2007 个）远胜 FA Free 的 regular（只有 169 个）。
但 Lucide 完全没有品牌 logo，FA 的 572 个 brands 是它不可替代的地方。
