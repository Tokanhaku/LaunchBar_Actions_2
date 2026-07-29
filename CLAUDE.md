# LaunchBar Actions 开发笔记

这个目录是 LaunchBar 的用户 action 目录（`~/Library/Application Support/LaunchBar/Actions`），同时是个 git repo。
下面是实际踩过坑总结出来的东西，动手前先看一遍，能省掉大量试错。

当前环境：LaunchBar 6.24 (build 6297) / macOS 26.5.2 Tahoe (Darwin 25) / Apple Silicon。
（Darwin 25 对应 macOS 26，不是 15；LaunchBar 6.24 是当前最新版，2026-04-27 发布。）

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
- remote：`git@github.com:Tokanhaku/LaunchBar_Actions_2.git`，只有 `main` 一个分支，直接提交到 main

### 图标约定（已统一，新写 action 照这个来）

**`symbol:` 是默认选择**，只有 SF Symbols 确实没有的品牌 logo 才用 bundle 内的 Template PNG
（现存 5 个：obsidian / claude / deepl / gemini / feather）。`font-awesome:` 前缀已从整个仓库清除。

固定语义，别混用：

| 场景 | 图标 |
|---|---|
| 脚本报错、命令返回非零 | `symbol:exclamationmark.triangle` |
| 搜索正常跑完但没匹配（"No result!"） | `symbol:exclamationmark.magnifyingglass` |

这两个**必须保持不同** —— 同一个 action 里两种状态都可能出现，图标一样的话就分辨不出是搜索挂了还是单纯没结果。

**用任何 SF Symbol 之前先验证它存在**，名字很容易想当然（`questionmark.magnifyingglass` 就不存在）：

```swift
NSImage(systemSymbolName: "exclamationmark.magnifyingglass", accessibilityDescription: nil) != nil
```

### 找无用图片时注意

**结果项的图标是写在脚本里的，不在 Info.plist 里。** 只 grep Info.plist 判断某个图片没人用，会误删。
必须连 `Contents/Scripts/` 一起 grep：

```sh
grep -rlF "$stem" "$action/Contents/Info.plist" "$action/Contents/Scripts"
```

现在还留在 bundle 里被脚本引用的有 `file-magnifying-glass-light_Template`（两个搜索 action 的结果项）
和 `obsidian_icon.png`（Search Obsidian Notes）。

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

---

## 8. 主题（Theme）

主题是 `.lbtheme` bundle，跟 action 一样是纯声明式的，可以自己写。

- 内置的 11 个在 `/Applications/LaunchBar.app/Contents/Resources/Themes/`，用户主题放
  `~/Library/Application Support/LaunchBar/Themes/`（双击 `.lbtheme` 也能装，app 注册了这个文档类型）
- 结构：`Contents/Info.plist`（只要 `CFBundleIdentifier` + `CFBundleName`）+ `Contents/Resources/Properties.plist` + 可选图片
- **继承靠 Properties.plist 里的显式 `parent` 键**（值是父主题的 bundle id），不是从点分 id 推导。
  没写 `parent` 就回落到 `Base`（Base 只提供图片，没有 Properties.plist；其余默认值编译在 app 里）
- **明暗配对是给 id 追加 `.dark`**：`X` 的深色版必须是 `X.dark`，LaunchBar 会跟随系统外观自动切
- 当前选择存在 `defaults` 的 `at.obdev.LaunchBar` → `Theme` 键（值是 bundle id）。
  **LaunchBar 退出时会回写 defaults，所以要改这个键必须先退出 LaunchBar**
- 改主题要重启 LaunchBar 才重新扫描（配置里有 `ODLBThemesRule`，主题也进索引，能直接输名字切换）

### Properties.plist 语法

约 260 个键，前缀分四组：`window*` / `inputArea*` / `itemList*` / `textInput*`，外加 `default*`（共享基色/字体）
和 `templateIcon*`。取全量键名：

```sh
strings -a /Applications/LaunchBar.app/Contents/MacOS/LaunchBar \
  | grep -E "^(window|inputArea|itemList|text|template|default)[A-Za-z0-9@]*$" | sort -u
```

- 自定义键 + `@名字` 引用（内置主题用 `brightBlue` / `searchColor` 这种）
- 表达式支持 `+` `-` `*`：`"@defaultTextColor + 0.1"`、`"@itemListSelectionHighlightColor - 0.3"`
- 任何键都能加 `@1x` / `@2x` 后缀区分分辨率
- 颜色三种写法：`"0 0 0 0.5"`（rgba 0–1）/ `"#00000080"` / `clearColor`、`whiteColor`
- 还有 edge insets `"6 6 6 6"` / point / rect / size / gradient（`{"0.0": 色, "1.0": 色}`）/ 字体名 / 图片名
- 解析失败会 NSLog `Theme "%@", key "%@": Unable to parse …` 然后**静默回退**到黑色或系统字体

### Liquid Glass 的结论

**做不到真的。** LaunchBar 6.24 虽然是 SDK 26.0 编译的，但 `nm -arch arm64 -u` 里只有
`_OBJC_CLASS_$_NSVisualEffectView`，没有 `NSGlassEffectView`；主题里也没有任何键能换视图类，更不能塞代码。

能做的是仿玻璃：`windowBackgroundMaterial`（`NSVisualEffectMaterial` 原始枚举值，内置主题用过 1/2/21）+
低 alpha `windowBackgroundColor` + `windowCornerRadius`/`windowCornerShapeExponent`（连续圆角）+
`windowHasBorder`/`windowBorderColor` 的亮边 + `windowHasInnerShadow` 系列伪造厚度和高光 +
半透明 `itemListSelectionHighlightColor` 的胶囊选中。
拿不到的：折射/lensing、跟随指针的高光、形变动画、选中条自己的玻璃层。

自制的 `Glass` 主题（`Glass` + `Glass.dark`）就是按这套做的。生成脚本 `Themes/build_glass_themes.py`
在本 repo 里（这是唯一一个非 action 的目录），跑一遍会把两个 bundle 重新写进**同级的**
`~/Library/Application Support/LaunchBar/Themes/`（会覆盖同名的）。改完要退出 LaunchBar 再改
`Theme` 键，然后重启。

调这类主题时实测出来的四条，别再重新试一遍：

1. **material 0/1/2 是 legacy 的外观固定档**（`.appearanceBased`/`.light`/`.dark`）。
   `1` 在 dark mode 下**仍然发白** —— `.dark` 变体必须覆盖成 `2`（内置 `Default.dark` 就是这么干的）。
   3 以上的现代材质会自己适配外观，不用覆盖。
2. **Tahoe 上越"现代"的材质越不透**：`5` menu / `13` hudWindow / `21` underWindowBackground 都是重磨砂，
   看着几乎不透明；legacy `1`/`2` 反而最薄最通透。实测挑下来用的是 1/2。
3. **通透度唯一的旋钮是 `windowBackgroundColor` 的 alpha**。`windowBackgroundAlphaValue` /
   `windowBackgroundBlurRadius` / `windowBackgroundAppearance` 这几个 setter 在二进制里存在，
   但**没有对应的主题键字符串**，改不了；磨砂浓度是 AppKit 定的。
   白 5% / 黑 10% 是舒服的值，再往下（白 2%）肉眼已经看不出区别。
4. **明暗两边的边缘处理是反的**，别想着共用一套值：
   - 浅色：纯白的 `windowBorderColor` 会糊成一片雾，`windowInnerShadow`（blur 3）又会把边晕开。
     最后是一道**深色 1px 发丝线**（`#00000040`，`windowBorderWidth` **0.5** —— Retina 上 1pt = 2px 显粗）
     加 `windowHasInnerShadow: false`，去掉一切会晕边的东西才够利落。
   - 深色：反过来，边和内高光都用低透明度白（`#FFFFFF40` / `#FFFFFF33`，blur 3），这样才有厚度感。

   所以 `dark_props` 里把 `windowHasBorder` / `windowBorder*` / `windowHasInnerShadow` / `windowInnerShadow*`
   **全部显式钉死**，免得调浅色时把深色带跑。
5. **底透了要补文字描边，而且描边分区域**。半透明底上文字会被背景吃掉，内置主题的办法是给文字加白色描边
   （`defaultTextShadowColor`，Default 是白 33%）。
   **但 Default 把 `inputAreaTextShadowColor` 设成了 `clearColor`** —— 输入区（包括你输入的那串缩写字母）
   完全不吃 `defaultTextShadow*`，只认 `inputAreaTextShadow*`。改错地方会看着"改了没效果"。
   最后浅色用的是：缩写字母 `inputAreaAbbreviationTextColor` 黑 82%（原本继承 dimmed 的 50%）+
   `inputAreaTextShadowColor` 白 70% / blur 1.0。深色必须把这两个钉回 `clearColor` / `0`，
   白字底下垫白描边会发光。
