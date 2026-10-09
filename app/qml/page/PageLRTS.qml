import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0

FluScrollablePage {
    id: page
    title: qsTr("懒人听书")
    Component.onCompleted: Bridge.set_lrts_mode("app")

    RowLayout {
        width: parent.width
        Item {
            Layout.preferredWidth: 34
            Layout.preferredHeight: 34
            Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/user.svg"; fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        sourceSize.width: 96
                        sourceSize.height: 96 }
            MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: loginDialog.open(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("用户登录") }
        }
         FluButton {
             text: qsTr("打开下载目录")
             onClicked: Bridge.open_download_dir(currentAlbumTitle)
         }
         Item { Layout.fillWidth: true }
    }

    RowLayout {
        width: parent.width

        RowLayout {
            Layout.preferredWidth: Math.max(300, parent.width * 0.34)
            spacing: 8
            FluTextBox {
                id: searchBox
                Layout.fillWidth: true
                placeholderText: qsTr("请输入搜索关键字")
                Keys.onReturnPressed: do_search()
                Keys.onEnterPressed: do_search()
            }
            Item {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/search.svg"; fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        sourceSize.width: 96
                        sourceSize.height: 96 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: do_search(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("搜索") }
            }
            Item {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/refresh.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: refresh_search(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("刷新") }
            }
        }

        Item { Layout.fillWidth: true }

        FluComboBox {
            id: qualityCombo
            Layout.preferredWidth: 150
            model: ["标准（约 1.6 MB）", "高清（约 6.2 MB）", "极致（约 9.0 MB）"]
            currentIndex: 0
            onActivated: currentQuality = index + 1
        }

        FluTextBox {
            id: rangeStartBox
            Layout.preferredWidth: 64
            placeholderText: qsTr("起始集")
            inputMethodHints: Qt.ImhDigitsOnly
        }
        Label { text: "-"; color: "#888" }
        FluTextBox {
            id: rangeEndBox
            Layout.preferredWidth: 64
            placeholderText: qsTr("结束集")
            inputMethodHints: Qt.ImhDigitsOnly
        }
        FluButton {
            text: qsTr("分区下载")
            onClicked: download_range()
        }
         FluButton {
             text: qsTr("全部下载")
             onClicked: download_all()
         }
    }

    FluPopup {
        id: loginDialog
        implicitWidth: 760
        implicitHeight: 430
        property int selectedMode: 0
        onOpened: {
            selectedMode = 0
            Bridge.set_lrts_mode("app")
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 20

            ColumnLayout {
                Layout.preferredWidth: 180
                Layout.fillHeight: true
                spacing: 8

                FluText {
                    text: qsTr("登录方式")
                    font: FluTextStyle.Title
                    Layout.bottomMargin: 8
                }

                ButtonGroup { id: loginModes }
                RadioButton {
                    text: qsTr("移动端 App")
                    checked: true
                    ButtonGroup.group: loginModes
                                     onClicked: {
                        loginDialog.selectedMode = 0
                        Bridge.set_lrts_mode("app")
                    }
                }
                RadioButton {
                    text: qsTr("微信小程序")
                    ButtonGroup.group: loginModes
                                     onClicked: {
                        loginDialog.selectedMode = 1
                        Bridge.set_lrts_mode("wechat")
                    }
                }
                RadioButton {
                    text: qsTr("Web")
                    ButtonGroup.group: loginModes
                                     onClicked: {
                        loginDialog.selectedMode = 2
                        Bridge.set_lrts_mode("web")
                    }
                }
                Item { Layout.fillHeight: true }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: FluTheme.dark ? "#454545" : "#dddddd"
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                FluText {
                    text: loginDialog.selectedMode === 0 ? qsTr("移动端 App 认证")
                        : loginDialog.selectedMode === 1 ? qsTr("微信小程序会话")
                        : qsTr("Web 会话")
                    font: FluTextStyle.Title
                }

                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: loginDialog.selectedMode

                    ColumnLayout {
                        spacing: 10
                        FluText {
                            text: qsTr("粘贴 Reqable 导出的 App 认证 JSON。")
                            color: FluTheme.fontSecondaryColor
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        ScrollView {
                            id: lrtsAuthScroll
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            ScrollBar.horizontal.policy: ScrollBar.AsNeeded

                            TextArea {
                                id: lrtsAuthBox
                                width: Math.max(lrtsAuthScroll.width, contentWidth + 24)
                                height: Math.max(lrtsAuthScroll.height, contentHeight + 24)
                                placeholderText: qsTr("认证 JSON")
                                wrapMode: TextEdit.NoWrap
                                selectByMouse: true
                                persistentSelection: true
                                font.family: "Consolas"
                                font.pixelSize: 12
                                color: FluTheme.dark ? "#e6e6e6" : "#202020"
                                selectionColor: FluTheme.dark ? "#395f8a" : "#b8d7f5"
                                background: Rectangle {
                                    radius: 4
                                    border.width: 1
                                    border.color: FluTheme.dark ? "#555555" : "#c8c8c8"
                                    color: FluTheme.dark ? "#1e1e1e" : "#fafafa"
                                }
                                Component.onCompleted: text = Bridge.get_lrts_auth()
                            }
                        }
                    }

                    ColumnLayout {
                        spacing: 10
                        RowLayout {
                            FluButton {
                                text: qsTr("打开微信 H5 登录")
                                onClicked: Bridge.open_wechat_login()
                            }
                            Image {
                                source: "qrc:/qml/res/refresh.svg"
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        sourceSize.width: 96
                        sourceSize.height: 96
                            }
                            FluButton {
                                text: qsTr("检测登录状态")
                                onClicked: Bridge.check_login_status()
                            }
                        }
                        FluText {
                            text: qsTr("在内置页面完成登录后，可粘贴 Cookie 手动应用。")
                            color: FluTheme.fontSecondaryColor
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        FluTextBox {
                            id: wechatCookieBox
                            Layout.fillWidth: true
                            placeholderText: qsTr("微信 H5 Cookie")
                        }
                    }

                    ColumnLayout {
                        spacing: 10
                        RowLayout {
                            FluButton {
                                text: qsTr("内置 Web 登录")
                                onClicked: Bridge.open_web_login()
                            }
                            Image {
                                source: "qrc:/qml/res/refresh.svg"
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        sourceSize.width: 96
                        sourceSize.height: 96
                            }
                            FluButton {
                                text: qsTr("检测登录状态")
                                onClicked: Bridge.check_login_status()
                            }
                        }
                        FluText {
                            text: qsTr("也可以粘贴从浏览器请求中获取的 Web Cookie。")
                            color: FluTheme.fontSecondaryColor
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                        FluTextBox {
                            id: webCookieBox
                            Layout.fillWidth: true
                            placeholderText: qsTr("Web Cookie")
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                     Item { Layout.fillWidth: true }
                    FluButton {
                        text: qsTr("取消")
                        onClicked: loginDialog.close()
                    }
                    FluButton {
                        text: qsTr("应用")
                                         onClicked: {
                            if (loginDialog.selectedMode === 0) {
                                var authText = lrtsAuthBox.text.trim()
                                if (!authText) {
                                    statusLabel.text = qsTr("请输入 App 认证 JSON")
                                    return
                                }
                                try {
                                    var parsedAuth = JSON.parse(authText)
                                    lrtsAuthBox.text = JSON.stringify(parsedAuth, null, 2)
                                    Bridge.set_lrts_auth(lrtsAuthBox.text)
                                } catch (e) {
                                    statusLabel.text = qsTr("认证 JSON 解析失败：") + e
                                    return
                                }
                            } else {
                                var cookieText = loginDialog.selectedMode === 1
                                    ? wechatCookieBox.text.trim() : webCookieBox.text.trim()
                                if (!cookieText) {
                                    statusLabel.text = qsTr("请输入对应模式的 Cookie")
                                    return
                                }
                                Bridge.set_cookie(cookieText)
                            }
                            loginDialog.close()
                        }
                    }
                }
            }
        }
    }

    RowLayout {
        id: contentRow
        width: parent.width
        height: 420
        spacing: 12

        // ============ 搜索结果列表 ============
        Rectangle {
            id: searchRow
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            radius: 8
            color: FluTheme.dark ? Qt.rgba(0,0,0,0.2) : Qt.rgba(1,1,1,0.6)

        RowLayout {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 8
            height: 24
            Label {
                text: qsTr("搜索结果")
                font.pixelSize: 13
                color: FluTheme.dark ? "white" : "#333"
            }
            FluProgressRing {
                id: searchLoading
                visible: false
                Layout.preferredWidth: 18
                Layout.preferredHeight: 18
            }
            Item { Layout.fillWidth: true }
        }

        ListView {
            id: resultList
            anchors.fill: parent
            anchors.margins: 8
            anchors.topMargin: 30
            model: ListModel { id: resultModel }
            clip: true
            delegate: FluItemDelegate {
                width: ListView.view.width
                height: 48
                 background: Rectangle {
                     radius: 4
                     color: resultList.currentIndex === index ? (FluTheme.dark ? "#354b60" : "#dceeff") : (hovered ? (FluTheme.dark ? "#2f3b46" : "#e8f2fc") : "transparent")
                 }
                 onClicked: {
                     resultList.currentIndex = index
                     trackModel.clear()
                     statusLabel.text = qsTr("正在加载曲目...")
                    searchLoading.visible = true
                     Bridge.load_album_lrts(bookId)
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    FluIcon {
                        Layout.preferredWidth: 20
                        iconSource: iconName === "anchor" ? FluentIcons.Contact : FluentIcons.MusicNote
                    }
                    Column {
                        Layout.fillWidth: true
                        Label { text: title; font.pixelSize: 13 }
                        Label { text: subtitle; font.pixelSize: 11; color: "#888" }
                    }
                }
            }
        }
    }

    // ============ 专辑曲目列表 ============
    Rectangle {
        id: trackPanel
        Layout.fillWidth: true
        Layout.preferredWidth: 2
        Layout.fillHeight: true
        radius: 8
        color: FluTheme.dark ? Qt.rgba(0,0,0,0.2) : Qt.rgba(1,1,1,0.6)

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: qsTr("曲目列表")
                    font.pixelSize: 13
                    color: FluTheme.dark ? "white" : "#333"
                }
                Item { Layout.fillWidth: true }
                FluProgressRing {
                    id: loading
                    visible: false
                    Layout.preferredWidth: 120
                }
            }

            RowLayout {
                Layout.fillWidth: true
                CheckBox {
                    id: pageSelectAll
                    text: qsTr("全选本页")
                    width: 18
                    height: 18
                    scale: 0.78
                    checked: pageSelectionState()
                    onClicked: setPageChecked(checked)
                }
                Label { text: qsTr("每页 50 集"); color: "#888" }
                Item { Layout.fillWidth: true }
            }

            ListView {
                id: trackList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: ListModel { id: trackModel }
                ScrollBar.vertical: ScrollBar {
                    id: trackScrollBar
                    width: 6
                    policy: ScrollBar.AsNeeded
                    interactive: true
                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: 3
                        color: FluTheme.dark ? "#777777" : "#aaaaaa"
                        opacity: trackScrollBar.pressed || trackScrollBar.hovered ? 0.9 : 0.45
                    }
                    background: Rectangle {
                        implicitWidth: 6
                        color: "transparent"
                    }
                }
                 property int pageSize: 50
                 property int currentPage: 1
                property int totalPages: 1
                delegate: FluItemDelegate {
                    width: ListView.view.width
                    visible: index >= (trackList.currentPage - 1) * trackList.pageSize
                             && index < trackList.currentPage * trackList.pageSize
                    height: visible ? 40 : 0
                     background: Rectangle {
                         radius: 4
                         color: trackList.currentIndex === index ? (FluTheme.dark ? "#354b60" : "#dceeff") : (hovered ? (FluTheme.dark ? "#2f3b46" : "#e8f2fc") : "transparent")
                     }
                                     onClicked: {
                        trackList.currentIndex = index
                        player_play()
                    }
                    RowLayout {
                        anchors.left: parent.left
                         anchors.right: parent.right
                         anchors.verticalCenter: parent.verticalCenter
                         height: parent.height
                         anchors.leftMargin: 8
                         anchors.rightMargin: 8
                        CheckBox {
                            id: trackCheck
                            width: 18
                            height: 18
                            scale: 0.78
                            checked: model.checked
                            onClicked: trackModel.setProperty(index, "checked", checked)
                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.LeftButton
                                property bool draggingSelection: false
                                onPressed: {
                                    draggingSelection = true
                                    var next = !trackCheck.checked
                                    trackModel.setProperty(index, "checked", next)
                                }
                                onEntered: {
                                    if (draggingSelection)
                                        trackModel.setProperty(index, "checked", trackCheck.checked)
                                }
                                onReleased: draggingSelection = false
                            }
                        }
                        Label { text: index + 1; width: 40; color: "#888" }
                        Label { text: title; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: duration; color: "#888" }
                         Label { text: status; color: status === "无权限" ? "#d9534f" : (status === "下载中" ? "#d99000" : "#4a9b62"); Layout.preferredWidth: 56; horizontalAlignment: Text.AlignHCenter }
                    }
                }
            }

            // 分页与下载操作
            RowLayout {
                Layout.fillWidth: true
                FluButton {
                    text: qsTr("上一页")
                    enabled: trackList.currentPage > 1
                                     onClicked: {
                        trackList.currentPage--
                        pagePicker.currentIndex = trackList.currentPage - 1
                    }
                }
                FluComboBox {
                    id: pagePicker
                    Layout.preferredWidth: 82
                    model: pageOptions()
                    onActivated: trackList.currentPage = index + 1
                }
                Label { text: "/ " + trackList.totalPages; color: "#888" }
                FluButton {
                    text: qsTr("下一页")
                    enabled: trackList.currentPage < trackList.totalPages
                                     onClicked: {
                        trackList.currentPage++
                        pagePicker.currentIndex = trackList.currentPage - 1
                    }
                }
                Item { Layout.fillWidth: true }
FluButton {
                      text: qsTr("下载选中")
                      onClicked: download_selected()
                  }
                  FluButton {
                      text: loading.visible ? qsTr("加载中...") : qsTr("加载全部")
                     onClicked: { loading.visible = true; statusLabel.text = qsTr("正在加载全部曲目..."); Bridge.load_all_album_lrts(currentAlbumId) }
                 }
                 }
        }
    }
    }

    // ============ 播放控制 ============
    ColumnLayout {
        id: playerControl
        parent: page
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.bottomMargin: 12
        height: 136
        z: 100
        spacing: 2
        Item {
            Layout.fillWidth: true
            height: 38
            Label {
                id: statusLabel
                anchors.fill: parent
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.WordWrap
                text: qsTr("就绪")
                color: "#888"
            }
        }
        Item {
            Layout.fillWidth: true
            height: 48
            Row {
                anchors.centerIn: parent
                spacing: 6
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: FluTheme.dark ? "qrc:/qml/res/player-prev-dark.svg" : "qrc:/qml/res/player-prev.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: player_prev(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("上一集") }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: playerPlaying ? (FluTheme.dark ? "qrc:/qml/res/player-pause-dark.svg" : "qrc:/qml/res/player-pause.svg") : (FluTheme.dark ? "qrc:/qml/res/player-play-dark.svg" : "qrc:/qml/res/player-play.svg"); fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (playerPlaying)
                                player_pause()
                            else
                                player_play()
                        }
                        ToolTip.visible: containsMouse
                        ToolTip.text: playerPlaying ? qsTr("暂停") : qsTr("继续")
                    }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: FluTheme.dark ? "qrc:/qml/res/player-next-dark.svg" : "qrc:/qml/res/player-next.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: player_next(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("下一集") }
                }
            }
            RowLayout {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                Label { text: qsTr("音量"); color: "#888" }
                Slider {
                     id: volumeSlider
                     Layout.preferredWidth: 130
                     from: 0
                     to: 1
                     value: 1.0
                     handle: Rectangle {
                         implicitWidth: 10
                         implicitHeight: 10
                         radius: 5
                         color: FluTheme.dark ? "#d0d0d0" : "#666666"
                         x: volumeSlider.leftPadding + volumeSlider.visualPosition * (volumeSlider.availableWidth - width)
                         y: volumeSlider.topPadding + volumeSlider.availableHeight / 2 - height / 2
                     }
                     onMoved: Bridge.player_set_volume(value)
                 }
            }
        }
        Item {
            Layout.fillWidth: true
            height: 24
            RowLayout {
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(parent.width * 0.465, 570)
                Label { text: fmt_ms(playerPosition); color: "#888" }
                Slider { id: playerSlider; Layout.fillWidth: true; from: 0; to: Math.max(1, playerDuration); value: playerPosition; onMoved: Bridge.player_seek(Math.round(value)) }
                Label { text: fmt_ms(playerDuration); color: "#888" }
            }
        }
    }

    property bool playerPlaying: false
    property int playerPosition: 0
    property int playerDuration: 0

    // ============ 逻辑 ============
    property string currentAlbumId: ""
    property string currentAlbumTitle: ""
    property var currentTracks: []
    property string saveDir: ""
    property int currentQuality: 1

    function quality_name(value) {
        var names = ["", "标准", "高清", "极致"]
        return names[Math.max(1, Math.min(3, parseInt(value || 1)))]
    }

    function do_search() {
        var kw = searchBox.text.trim()
        if (kw === "") { statusLabel.text = "请输入搜索关键字"; return }
        statusLabel.text = "搜索中..."
        searchLoading.visible = true
        // 超时处理：15 秒无响应则提示
        searchTimer.restart()
        Bridge.search_lrts(kw)
    }

    function refresh_search() {
        var kw = searchBox.text.trim()
        if (kw === "") { statusLabel.text = qsTr("请输入搜索关键字"); return }
        searchLoading.visible = true
        searchTimer.restart()
        Bridge.refresh_search_lrts(kw)
    }

    Timer {
        id: searchTimer
        interval: 45000
        repeat: false
        onTriggered: {
            statusLabel.text = "搜索超时，请检查网络后重试"
            searchLoading.visible = false
        }
    }

    // 监听桥接信号
    Connections {
        target: Bridge
        function onLoginStatus(message) {
            statusLabel.text = message
        }

        function onMessage(title, content) {
            statusLabel.text = title + "：" + content
        }

        function onLrtsTrackStatus(section, value) {
            for (var i = 0; i < trackModel.count; i++) {
                if (String(trackModel.get(i).section) === String(section)) {
                    trackModel.setProperty(i, "status", value)
                    break
                }
            }
        }
        function onSearchDone(platform, result) {
            searchTimer.stop()
            searchLoading.visible = false
            if (platform !== "lrts") return
            if (!result.ok) { statusLabel.text = "搜索失败：" + (result.error || "未知错误"); return }
            resultModel.clear()
            var books = result.books || []
            var anchors = result.anchors || []
            for (var i = 0; i < books.length; i++) {
                resultModel.append({
                    title: books[i].name || "",
                    subtitle: books[i].subTitle || "",
                    bookId: String(books[i].id || ""),
                    iconName: "book"
                })
            }
            for (var j = 0; j < anchors.length; j++) {
                resultModel.append({
                    title: anchors[j].name || "",
                    subtitle: anchors[j].description || "",
                    bookId: String(anchors[j].userId || ""),
                    iconName: "anchor"
                })
            }
            statusLabel.text = "搜索完成：" + (books.length + anchors.length) + " 条"
        }

        function onAlbumLoaded(result) {
            searchLoading.visible = false
            loading.visible = false
            if (!result.ok) { statusLabel.text = "分析失败: " + (result.error || ""); return }
            currentAlbumId = String(result.albumId || (result.album && result.album.id) || "")
            currentAlbumTitle = (result.album && result.album.name) || ""
            currentTracks = []
            var rawTracks = result.tracks || []
            for (var t = 0; t < rawTracks.length; t++) {
                var raw = rawTracks[t]
                currentTracks.push({
                    title: raw.title || raw.name || "",
                    trackId: String(raw.trackId || raw.tmeId || raw.id || ""),
                    resId: String(raw.resId || raw.id || raw.sectionId || ""),
                    section: parseInt(raw.section || t + 1),
                    length: raw.length || raw.duration || 0,
                    size: raw.size || 0,
                    hqMedias: raw.hqMedias
                })
            }
            trackModel.clear()
            for (var i = 0; i < currentTracks.length; i++) {
                trackModel.append({
                    title: currentTracks[i].title || currentTracks[i].name || "",
                    trackId: currentTracks[i].trackId,
                    resId: currentTracks[i].resId,
                    section: parseInt(currentTracks[i].section || i + 1),
                    albumId: currentAlbumId,
                    duration: fmt_duration(currentTracks[i].length || currentTracks[i].duration || 0),
                    checked: false
                })
            }
            trackList.totalPages = Math.max(1, Math.ceil(trackModel.count / trackList.pageSize))
            trackList.currentPage = 1
            pagePicker.currentIndex = 0
            statusLabel.text = "分析完成：" + currentAlbumTitle + " 共 " + trackModel.count + " 集"
        }

        function onPlayUrlReady(result) {
            if (!result.ok) {
                if (trackList.currentIndex >= 0 && trackList.currentIndex < trackModel.count)
                    trackModel.setProperty(trackList.currentIndex, "status", "无权限")
                statusLabel.text = "获取播放地址失败：" + (result.error || "未返回错误详情")
                return
            }
            statusLabel.text = "正在播放（" + quality_name(result.quality || currentQuality) + "音质）"
        }
        function onPlayerPositionChanged(value) { playerPosition = value }
        function onPlayerDurationChanged(value) { playerDuration = value }
        function onPlayerStateChanged(value) {
            playerPlaying = value === "playing"
            if (value === "playing") statusLabel.text = "正在播放"
            else if (value === "paused") statusLabel.text = "已暂停"
        }
        function onPlayerError(message) { statusLabel.text = "播放失败：" + message }
    }

    function fmt_duration(sec) {
        sec = parseInt(sec || 0)
        var m = Math.floor(sec / 60), s = sec % 60
        return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s)
    }

    function pageOptions() {
        var values = []
        for (var i = 1; i <= trackList.totalPages; i++) values.push(String(i))
        return values
    }

    function pageSelectionState() {
        if (trackModel.count === 0) return false
        var first = (trackList.currentPage - 1) * trackList.pageSize
        var last = Math.min(trackModel.count, first + trackList.pageSize)
        if (first >= last) return false
        for (var i = first; i < last; i++) {
            if (!trackModel.get(i).checked) return false
        }
        return true
    }

    function setPageChecked(value) {
        var first = (trackList.currentPage - 1) * trackList.pageSize
        var last = Math.min(trackModel.count, first + trackList.pageSize)
        for (var i = first; i < last; i++) trackModel.setProperty(i, "checked", value)
    }

    function download_selected() {
        var secArr = []
        for (var i = 0; i < currentTracks.length; i++) {
            var item = currentTracks[i]
            if (trackModel.get(i).checked) {
                secArr.push({section: item.section, resId: item.resId,
                    trackId: item.trackId, name: item.title || ""})
            }
        }
        if (secArr.length === 0) {
            statusLabel.text = "请先勾选要下载的曲目"
            return
        }
        statusLabel.text = "准备下载选中曲目 " + secArr.length + " 集..."
        Bridge.download_batch_lrts(currentAlbumId, JSON.stringify(secArr), currentQuality, saveDir, currentAlbumTitle)
    }
    function download_all() {
        if (currentTracks.length === 0) {
            statusLabel.text = "请先搜索并加载专辑"
            return
        }
        var secArr = []
        for (var i = 0; i < currentTracks.length; i++) {
            secArr.push({
                section: currentTracks[i].section,
                resId: currentTracks[i].resId,
                trackId: currentTracks[i].trackId,
                name: currentTracks[i].title || ""
            })
        }
        statusLabel.text = "准备全部下载 " + secArr.length + " 集（" + quality_name(currentQuality) + "音质）..."
        Bridge.download_batch_lrts(currentAlbumId, JSON.stringify(secArr), currentQuality, saveDir, currentAlbumTitle)
    }

    function download_range() {
        var start = parseInt(rangeStartBox.text)
        var end = parseInt(rangeEndBox.text)
        if (isNaN(start) || isNaN(end) || start > end) {
            statusLabel.text = "请输入有效的起始集和结束集"
            return
        }
        var secArr = []
        for (var i = 0; i < currentTracks.length; i++) {
            var item = currentTracks[i]
            var section = parseInt(item.section)
            if (section >= start && section <= end) {
                secArr.push({section: section, resId: item.resId,
                    trackId: item.trackId, name: item.title || ""})
            }
        }
        if (secArr.length === 0) {
            statusLabel.text = "指定范围内没有章节"
            return
        }
        statusLabel.text = "准备分区下载 " + secArr.length + " 集（" + quality_name(currentQuality) + "音质）..."
        Bridge.download_batch_lrts(currentAlbumId, JSON.stringify(secArr), currentQuality, saveDir, currentAlbumTitle)
    }

    function fmt_ms(ms) {
        ms = parseInt(ms || 0)
        var total = Math.floor(ms / 1000), m = Math.floor(total / 60), s = total % 60
        return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s)
    }

    function player_play() {
        var row = trackList.currentIndex
        if (row < 0 || row >= trackModel.count) {
            statusLabel.text = "请先选择曲目"
            return
        }
        var item = trackModel.get(row)
        statusLabel.text = "获取播放地址..."
        Bridge.get_play_url_lrts(item.trackId, item.resId, String(item.section), item.albumId, currentQuality)
    }
    function player_pause() { Bridge.player_pause() }
    function player_prev() {
        if (trackList.currentIndex > 0) {
            trackList.currentIndex--
            player_play()
        }
    }
    function player_next() {
        if (trackList.currentIndex + 1 < trackModel.count) {
            trackList.currentIndex++
            player_play()
        }
    }
}
