import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0

FluScrollablePage {
    id: page
    title: qsTr("喜马拉雅")

    // ============ 标题与登录 ============
    RowLayout {
        width: parent.width
        Label {
            text: qsTr("喜马拉雅")
            font.pixelSize: 18
            font.bold: true
            color: FluTheme.dark ? "#f5f5f5" : "#252525"
        }
        Item {
            Layout.preferredWidth: 34
            Layout.preferredHeight: 34
            Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/user.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
            MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: Bridge.open_ximalaya_login(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("用户登录") }
        }
        Item { Layout.fillWidth: true }
    }

    // ============ 搜索与下载操作 ============
    RowLayout {
        width: parent.width
        RowLayout {
            Layout.preferredWidth: Math.max(300, parent.width * 0.34)
            spacing: 8
            FluTextBox {
                id: albumUrlBox
                Layout.fillWidth: true
                placeholderText: qsTr("输入喜马拉雅专辑网址或ID")
                Keys.onReturnPressed: do_parse()
                Keys.onEnterPressed: do_parse()
            }
            Item {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/search.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: do_parse(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("分析专辑") }
            }
            Item {
                Layout.preferredWidth: 34
                Layout.preferredHeight: 34
                Image { anchors.centerIn: parent; width: 18; height: 18; source: "qrc:/qml/res/refresh.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: refresh_parse(); ToolTip.visible: containsMouse; ToolTip.text: qsTr("刷新") }
            }
        }
        Item { Layout.fillWidth: true }
        FluComboBox {
            id: qualityCombo
            Layout.preferredWidth: 150
            model: ["标准音质", "高清音质"]
            currentIndex: 0
        }
        FluButton { text: qsTr("下载选中"); onClicked: xmStatus.text = "下载功能（Python 侧）" }
        FluButton { text: qsTr("加载全部"); onClicked: xmShowAll = true }
    }

    // ============ 搜索结果与曲目列表 ============
    RowLayout {
        id: xmContentRow
        width: parent.width
        height: 420
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            radius: 8
            color: FluTheme.dark ? Qt.rgba(0,0,0,0.2) : Qt.rgba(1,1,1,0.6)
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                Label { text: qsTr("搜索结果"); font.pixelSize: 13 }
                Label {
                    text: xmAlbumTitle === "" ? qsTr("输入专辑网址或 ID 后点击分析") : xmAlbumTitle
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    color: FluTheme.dark ? "white" : "#333"
                }
                Item { Layout.fillHeight: true }
            }
        }

        Rectangle {
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
                Label { text: qsTr("专辑曲目"); font.pixelSize: 13 }
                Item { Layout.fillWidth: true }
                FluProgressRing {
                    id: xmLoading
                    visible: false
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 20
                }
                Label { id: xmStatus; color: "#888" }
            }

            ListView {
                id: xmTrackList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: ListModel { id: xmTrackModel }
                delegate: FluItemDelegate {
                    width: ListView.view.width
                     height: (xmShowAll || index < 10) ? 40 : 0
                     visible: xmShowAll || index < 10
                     background: Rectangle {
                         radius: 4
                         color: xmCurrentTrackIndex === index ? (FluTheme.dark ? "#354b60" : "#dceeff") : (hovered ? (FluTheme.dark ? "#2f3b46" : "#e8f2fc") : "transparent")
                     }
                    onClicked: {
                        xmCurrentTrackIndex = index
                         xmTrackList.currentIndex = index
                        xmPlayerStatus.text = title
                        Bridge.get_track_url_ximalaya(trackId, qualityCombo.currentIndex === 0 ? 1 : 2)
                    }
                    RowLayout {
                        anchors.left: parent.left
                         anchors.right: parent.right
                         anchors.verticalCenter: parent.verticalCenter
                         height: parent.height
                         anchors.leftMargin: 8
                         anchors.rightMargin: 8
                        Label { text: index + 1; width: 40; color: "#888" }
                        Label { text: title; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: duration; color: "#888" }
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
                    MouseArea { anchors.fill: parent; onClicked: xm_play_relative(-1); ToolTip.visible: containsMouse; ToolTip.text: qsTr("上一集") }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: xmPlaying ? (FluTheme.dark ? "qrc:/qml/res/player-pause-dark.svg" : "qrc:/qml/res/player-pause.svg") : (FluTheme.dark ? "qrc:/qml/res/player-play-dark.svg" : "qrc:/qml/res/player-play.svg"); fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (xmPlaying)
                                Bridge.player_pause()
                            else
                                Bridge.player_play()
                        }
                        ToolTip.visible: containsMouse
                        ToolTip.text: xmPlaying ? qsTr("暂停") : qsTr("继续")
                    }
                }
                Item {
                    width: 42; height: 42
                    Image { width: 28; height: 28; anchors.centerIn: parent; source: FluTheme.dark ? "qrc:/qml/res/player-next-dark.svg" : "qrc:/qml/res/player-next.svg"; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true; sourceSize.width: 96; sourceSize.height: 96 }
                    MouseArea { anchors.fill: parent; onClicked: xm_play_relative(1); ToolTip.visible: containsMouse; ToolTip.text: qsTr("下一集") }
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
                    id: xmPlayerStatus
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
             Label { text: fmt_ms(xmPosition); color: "#888" }
             Slider { Layout.fillWidth: true; from: 0; to: Math.max(1, xmDuration); value: xmPosition; onMoved: Bridge.player_seek(Math.round(value)) }
             Label { text: fmt_ms(xmDuration); color: "#888" }
            }
        }
    }

    property bool xmPlaying: false
    property int xmPosition: 0
    property int xmDuration: 0
    property int xmCurrentTrackIndex: -1

    // ============ 逻辑 ============
    property bool xmShowAll: false
    property var xmTracks: []
    property string xmAlbumId: ""
    property string xmAlbumTitle: ""

    function do_parse() {
        var input = albumUrlBox.text.trim()
        if (input === "") { xmStatus.text = "请输入专辑网址"; return }
        xmLoading.visible = true
        xmStatus.text = "分析中..."
        xmTimer.restart()
        Bridge.parse_ximalaya_album(input)
    }

    function refresh_parse() {
        var input = albumUrlBox.text.trim()
        if (input === "") { xmStatus.text = "请输入专辑网址"; return }
        xmLoading.visible = true
        xmStatus.text = "刷新中..."
        xmTimer.restart()
        Bridge.refresh_ximalaya_album(input)
    }

    Timer {
        id: xmTimer
        interval: 20000
        repeat: false
        onTriggered: {
            xmStatus.text = "分析超时，请检查网络"
            xmLoading.visible = false
        }
    }

    Connections {
        target: Bridge
        function onLoginStatus(message) {
            xmStatus.text = message
        }

        function onAlbumLoaded(result) {
            xmTimer.stop()
            xmLoading.visible = false
            if (!result.ok) { xmStatus.text = "解析失败: " + (result.error || ""); return }
            xmAlbumId = (result.album && result.album.id) || ""
            xmAlbumTitle = (result.album && (result.album.title || result.album.name)) || albumUrlBox.text
            xmTracks = result.tracks || []
            xmShowAll = false
            xmTrackModel.clear()
            for (var i = 0; i < xmTracks.length; i++) {
                xmTrackModel.append({
                    title: xmTracks[i].title || "",
                    trackId: String(xmTracks[i].id || ""),
                    duration: fmt_duration(xmTracks[i].duration || 0)
                })
            }
            xmStatus.text = "分析完成：" + (result.album && result.album.title || "") + " 共 " + xmTrackModel.count + " 集"
        }

        function onPlayUrlReady(result) {
            xmStatus.text = result.ok ? "播放地址就绪" : "获取失败"
        }
    }

    function fmt_duration(sec) {
        sec = parseInt(sec || 0)
        var m = Math.floor(sec / 60), s = sec % 60
        return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s)
    }

    function fmt_ms(value) {
        var sec = Math.floor(parseInt(value || 0) / 1000)
        return fmt_duration(sec)
    }

    function xm_play_relative(delta) {
        var next = xmCurrentTrackIndex + delta
        if (next < 0 || next >= xmTrackModel.count) return
        var item = xmTrackModel.get(next)
        xmCurrentTrackIndex = next
        xmPlayerStatus.text = item.title
        Bridge.get_track_url_ximalaya(item.trackId, qualityCombo.currentIndex === 0 ? 1 : 2)
    }

    Connections {
        target: Bridge
        function onPlayerPositionChanged(value) { xmPosition = value }
        function onPlayerDurationChanged(value) { xmDuration = value }
        function onPlayerStateChanged(value) { xmPlaying = value === "playing" }
        function onPlayerError(message) { xmPlayerStatus.text = message }
    }
}
