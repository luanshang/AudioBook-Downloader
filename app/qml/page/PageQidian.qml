import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0

FluScrollablePage {
    id: page
    title: qsTr("起点")

    RowLayout {
        width: parent.width
        Label {
            text: qsTr("起点")
            font.pixelSize: 18
            font.bold: true
            color: FluTheme.dark ? "#f5f5f5" : "#252525"
        }
        Item {
            Layout.preferredWidth: 34
            Layout.preferredHeight: 34
            Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/user.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
            MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: qdLoginDialog.open(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("用户登录") }
        }
        Item { Layout.fillWidth: true }
    }

    FluPopup {
        id: qdLoginDialog
        implicitWidth: 700
        implicitHeight: 400
        property int selectedMode: 0
        onOpened: {
            selectedMode = 0
            qdCookieBox.text = Bridge.get_qidian_cookie()
        }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 24
            spacing: 20

            ColumnLayout {
                Layout.preferredWidth: 170
                Layout.fillHeight: true
                spacing: 8
                FluText { text: qsTr("登录方式"); font: FluTextStyle.Title; Layout.bottomMargin: 8 }
                ButtonGroup { id: qdLoginModes }
                RadioButton {
                    text: qsTr("网页扫码登录")
                    checked: qdLoginDialog.selectedMode === 0
                    ButtonGroup.group: qdLoginModes
                    onClicked: qdLoginDialog.selectedMode = 0
                }
                RadioButton {
                    text: qsTr("手动粘贴 Cookie")
                    checked: qdLoginDialog.selectedMode === 1
                    ButtonGroup.group: qdLoginModes
                    onClicked: qdLoginDialog.selectedMode = 1
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
                    text: qdLoginDialog.selectedMode === 0 ? qsTr("起点网页扫码登录") : qsTr("应用起点 Cookie")
                    font: FluTextStyle.Title
                }
                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: qdLoginDialog.selectedMode
                    ColumnLayout {
                        spacing: 12
                        FluText {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: FluTheme.fontSecondaryColor
                            text: qsTr("在内置起点网页完成扫码后，Cookie 会自动同步并保存到本机。起点账号认证与懒人听书的 App/微信凭证相互独立。")
                        }
                        FluButton { text: qsTr("打开起点扫码登录"); onClicked: Bridge.open_qidian_login() }
                        FluButton { text: qsTr("检测登录状态"); onClicked: Bridge.check_qidian_login_status() }
                        Label {
                            id: qdLoginStatus
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: FluTheme.fontSecondaryColor
                            text: qsTr("登录后会自动应用起点 Cookie")
                        }
                        Item { Layout.fillHeight: true }
                    }
                    ColumnLayout {
                        spacing: 10
                        FluText {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: FluTheme.fontSecondaryColor
                            text: qsTr("粘贴浏览器或抓包中起点域名的 Cookie。该凭证仅用于起点，不会覆盖懒人听书登录。")
                        }
                        ScrollView {
                            id: qdCookieScroll
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            TextArea {
                                id: qdCookieBox
                                width: Math.max(qdCookieScroll.width, contentWidth + 24)
                                height: Math.max(qdCookieScroll.height, contentHeight + 24)
                                placeholderText: qsTr("起点 Cookie")
                                wrapMode: TextEdit.NoWrap
                                selectByMouse: true
                                persistentSelection: true
                                font.family: "Consolas"
                                font.pixelSize: 12
                                background: Rectangle {
                                    radius: 4
                                    border.width: 1
                                    border.color: FluTheme.dark ? "#555555" : "#c8c8c8"
                                    color: FluTheme.dark ? "#1e1e1e" : "#fafafa"
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    FluButton { text: qsTr("取消"); onClicked: qdLoginDialog.close() }
                    FluButton {
                        text: qdLoginDialog.selectedMode === 0 ? qsTr("完成") : qsTr("应用 Cookie")
                        onClicked: {
                            if (qdLoginDialog.selectedMode === 1) {
                                var cookie = qdCookieBox.text.trim()
                                if (!cookie) {
                                    qdLoginStatus.text = qsTr("请输入起点 Cookie")
                                    return
                                }
                                Bridge.set_qidian_cookie(cookie)
                            }
                            qdLoginDialog.close()
                        }
                    }
                }
            }
        }
    }

    Connections {
        target: Bridge
        function onLoginStatus(text) { qdLoginStatus.text = text }
    }

    RowLayout {
        width: parent.width
        RowLayout {
            Layout.preferredWidth: Math.max(300, parent.width * 0.34)
            spacing: 8
            FluTextBox {
                id: qdSearchBox
                Layout.fillWidth: true
                placeholderText: qsTr("搜索起点听书书籍")
                Keys.onReturnPressed: do_search()
                Keys.onEnterPressed: do_search()
            }
            Item {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/search.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
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
        FluButton { text: qsTr("加载全部"); onClicked: qdShowAll = true }
    }

    RowLayout {
        id: qdContentRow
        width: parent.width
        height: 420
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            radius: 6
            color: FluTheme.dark ? Qt.rgba(0, 0, 0, 0.2) : Qt.rgba(1, 1, 1, 0.6)
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("搜索结果"); font.pixelSize: 13 }
                    FluProgressRing {
                        id: qdSearchLoading
                        visible: false
                        Layout.preferredWidth: 18
                        Layout.preferredHeight: 18
                    }
                    Item { Layout.fillWidth: true }
                    Label { text: qdResultModel.count > 0 ? qsTr("%1 本").arg(qdResultModel.count) : ""; color: "#888" }
                }
                ListView {
                    id: qdResultList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: ListModel { id: qdResultModel }
                    delegate: FluItemDelegate {
                        width: ListView.view.width
                        height: 50
                    background: Rectangle {
                        radius: 4
                        color: qdResultList.currentIndex === index ? (FluTheme.dark ? "#354b60" : "#dceeff") : (hovered ? (FluTheme.dark ? "#2f3b46" : "#e8f2fc") : "transparent")
                    }
                        onClicked: {
                            qdSearchLoading.visible = true
                            qdStatus.text = qsTr("正在加载章节...")
                            qdTimer.restart()
                            Bridge.load_book_qidian(adid)
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            FluIcon { iconSource: FluentIcons.ReadingMode; Layout.preferredWidth: 20 }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label { text: title; font.pixelSize: 13; elide: Text.ElideRight; Layout.fillWidth: true }
                                Label { text: author; font.pixelSize: 11; color: "#888" }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 2
            Layout.fillHeight: true
            radius: 6
            color: FluTheme.dark ? Qt.rgba(0, 0, 0, 0.2) : Qt.rgba(1, 1, 1, 0.6)
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("章节列表"); font.pixelSize: 13 }
                    Item { Layout.fillWidth: true }
                    FluProgressRing {
                        id: qdLoading
                        visible: false
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: 20
                    }
                    Label { id: qdStatus; color: "#888" }
                }
                ListView {
                    id: qdChapterList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: ListModel { id: qdChapterModel }
                    delegate: FluItemDelegate {
                        width: ListView.view.width
                        height: 38
                    background: Rectangle {
                        radius: 4
                        color: qdResultList.currentIndex === index ? (FluTheme.dark ? "#354b60" : "#dceeff") : (hovered ? (FluTheme.dark ? "#2f3b46" : "#e8f2fc") : "transparent")
                    }
                        onClicked: {
                            qdCurrentChapterIndex = index
                            qdPlayerStatus.text = title
                            Bridge.get_play_url_qidian(adid, acid)
                        }
                        RowLayout {
                            anchors.left: parent.left
                         anchors.right: parent.right
                         anchors.verticalCenter: parent.verticalCenter
                         height: parent.height
                         anchors.leftMargin: 8
                         anchors.rightMargin: 8
                            Label { text: index + 1; Layout.preferredWidth: 36; color: "#888" }
                            Label { text: title; Layout.fillWidth: true; elide: Text.ElideRight }
                        }
                    }
                }
            }
        }
    }

    ColumnLayout {
        id: playerControl
        parent: page
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.bottomMargin: 12
        height: 96
        z: 100
        spacing: 2
        Item {
            Layout.fillWidth: true
            height: 48
            Row {
                anchors.centerIn: parent
                spacing: 6
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: FluTheme.dark ? "qrc:/qml/res/player-prev-dark.svg" : "qrc:/qml/res/player-prev.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: qd_play_relative(-1); ToolTip.visible: containsMouse; ToolTip.text: qsTr("上一章") }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: qdPlaying ? (FluTheme.dark ? "qrc:/qml/res/player-pause-dark.svg" : "qrc:/qml/res/player-pause.svg") : (FluTheme.dark ? "qrc:/qml/res/player-play-dark.svg" : "qrc:/qml/res/player-play.svg"); fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (qdPlaying)
                                Bridge.player_pause()
                            else
                                Bridge.player_play()
                        }
                        ToolTip.visible: containsMouse
                        ToolTip.text: qdPlaying ? qsTr("暂停") : qsTr("继续")
                    }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: FluTheme.dark ? "qrc:/qml/res/player-next-dark.svg" : "qrc:/qml/res/player-next.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: qd_play_relative(1); ToolTip.visible: containsMouse; ToolTip.text: qsTr("下一章") }
                }
            }
        }
        Item {
            Layout.fillWidth: true
            height: 28
            ColumnLayout {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 0
                Label {
                    id: qdPlayerStatus
                    Layout.preferredWidth: 190
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    text: qsTr("就绪")
                    color: "#888"
                }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Label { text: qsTr("音量"); color: "#888" }
                    Slider { Layout.preferredWidth: 130; from: 0; to: 1; value: 0.8; onMoved: Bridge.player_set_volume(value) }
                }
            }
        }
        Item {
            Layout.fillWidth: true
            height: 24
            RowLayout {
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.min(parent.width * 0.465, 570)
             Label { text: fmt_ms(qdPosition); color: "#888" }
             Slider { Layout.fillWidth: true; from: 0; to: Math.max(1, qdDuration); value: qdPosition; onMoved: Bridge.player_seek(Math.round(value)) }
             Label { text: fmt_ms(qdDuration); color: "#888" }
            }
        }
    }

    property bool qdShowAll: false
    property string qdCurrentAdid: ""
    property int qdCurrentChapterIndex: -1
    property bool qdPlaying: false
    property int qdPosition: 0
    property int qdDuration: 0

    function do_search() {
        var kw = qdSearchBox.text.trim()
        if (kw === "") { qdStatus.text = qsTr("请输入关键字"); return }
        qdStatus.text = qsTr("搜索中...")
        qdSearchLoading.visible = true
        qdTimer.restart()
        Bridge.search_qidian(kw)
    }

    function refresh_search() {
        var kw = qdSearchBox.text.trim()
        if (kw === "") { qdStatus.text = qsTr("请输入关键字"); return }
        qdSearchLoading.visible = true
        qdTimer.restart()
        Bridge.refresh_search_qidian(kw)
    }

    function qd_play_relative(delta) {
        var next = qdCurrentChapterIndex + delta
        if (next < 0 || next >= qdChapterModel.count) return
        var item = qdChapterModel.get(next)
        qdCurrentChapterIndex = next
        qdPlayerStatus.text = item.title
        Bridge.get_play_url_qidian(item.adid, item.acid)
    }

    function fmt_ms(value) {
        var sec = Math.floor(parseInt(value || 0) / 1000)
        var min = Math.floor(sec / 60)
        var rem = sec % 60
        return (min < 10 ? "0" + min : min) + ":" + (rem < 10 ? "0" + rem : rem)
    }

    Timer {
        id: qdTimer
        interval: 15000
        repeat: false
        onTriggered: {
            qdStatus.text = qsTr("操作超时，请检查网络")
            qdSearchLoading.visible = false
            qdLoading.visible = false
        }
    }

    Connections {
        target: Bridge
        function onLoginStatus(message) { qdStatus.text = message }
        function onSearchDone(platform, result) {
            if (platform !== "qidian") return
            qdTimer.stop()
            qdSearchLoading.visible = false
            if (!result.ok) { qdStatus.text = qsTr("搜索失败：") + (result.error || ""); return }
            qdResultModel.clear()
            var books = result.books || []
            for (var i = 0; i < books.length; i++) {
                qdResultModel.append({
                    title: books[i].title || books[i].bookName || "",
                    author: books[i].author || "",
                    adid: String(books[i].adid || books[i].id || "")
                })
            }
            qdStatus.text = qsTr("搜索完成：%1 本").arg(books.length)
        }
        function onAlbumLoaded(result) {
            qdTimer.stop()
            qdLoading.visible = false
            qdSearchLoading.visible = false
            if (!result.ok) { qdStatus.text = qsTr("加载失败：") + (result.error || ""); return }
            var book = result.book || {}
            qdCurrentAdid = String(book.adid || "")
            var chapters = result.chapters || []
            qdChapterModel.clear()
            for (var i = 0; i < chapters.length; i++) {
                qdChapterModel.append({
                    title: chapters[i].title || chapters[i].chapterName || "",
                    adid: qdCurrentAdid,
                    acid: String(chapters[i].acid || chapters[i].id || "")
                })
            }
            qdStatus.text = qsTr("加载完成：%1，共 %2 章").arg(book.title || "").arg(chapters.length)
        }
        function onPlayUrlReady(result) { qdPlayerStatus.text = result.ok ? qdPlayerStatus.text : qsTr("获取播放地址失败") }
        function onPlayerPositionChanged(value) { qdPosition = value }
        function onPlayerDurationChanged(value) { qdDuration = value }
        function onPlayerStateChanged(value) { qdPlaying = value === "playing" }
        function onPlayerError(message) { qdPlayerStatus.text = message }
    }
}
