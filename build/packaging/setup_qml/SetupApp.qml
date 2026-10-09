import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt5Compat.GraphicalEffects
import FluentUI 1.0

FluWindow {
    id: window
    title: "有声书下载器 v0.0.1 安装"
    width: 760
    height: 500
    fixSize: true
    fitsAppBarWindows: true
    launchMode: FluWindowType.SingleTask

    appBar: FluAppBar {
        width: window.width
        height: 30
        title: "有声书下载器 安装向导"
        showDark: true
        darkClickListener: function(btn) {
            var next = FluTheme.darkMode === FluThemeType.DarkMode.Dark
                ? FluThemeType.DarkMode.Light : FluThemeType.DarkMode.Dark
            FluTheme.darkMode = next
        }
    }

    property int currentPage: 0
    property string installDir: ""
    property bool makeShortcut: true
    property bool launchAfter: true
    property string statusText: "准备安装"
    property double progressValue: 0

    Connections {
        target: Installer
        function onProgressChanged(value, text) {
            window.progressValue = value
            window.statusText = text
        }
        function onInstallFinished() {
            window.installDir = Installer.installDir
            window.currentPage = 3
            backButton.visible = false
            cancelButton.visible = false
            nextButton.enabled = true
        }
    }

    // 主体内容：4 个页面用 StackLayout 切换
    StackLayout {
        id: pages
        anchors.fill: parent
        anchors.margins: 16
        currentIndex: window.currentPage

        // ---- 页 0：欢迎 ----
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                // 产品图标：16:9 自适应宽度，跟随明暗主题；宽度为父级 28%
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.preferredHeight: width * 9 / 16
                    Layout.maximumWidth: 300
                    clip: true
                    Image {
                        id: heroIcon
                        anchors.fill: parent
                        source: "res/icon.svg"
                        sourceSize: Qt.size(width, height)
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        visible: false
                    }
                    ColorOverlay {
                        anchors.fill: heroIcon
                        source: heroIcon
                        color: FluTheme.fontPrimaryColor
                    }
                }

                Item { height: 4 }
                Text {
                    text: "欢迎安装 有声书下载器"
                    font.pixelSize: 22
                    font.bold: true
                    color: FluTheme.fontPrimaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Text {
                    text: "版本 v0.0.1"
                    font.pixelSize: 13
                    color: FluTheme.fontSecondaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Item { height: 4 }
                Text {
                    text: "基于 PySide6 + FluentUI 的多平台有声内容检索、试听与下载工具，支持懒人听书、喜马拉雅、起点畅听。"
                    font.pixelSize: 13
                    color: FluTheme.fontSecondaryColor
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                    Layout.maximumWidth: 560
                    Layout.alignment: Qt.AlignHCenter
                }
                Item { height: 2 }
                Text {
                    text: "安装向导将把程序安装到本机，并可创建桌面快捷方式。点击“下一步”继续。"
                    font.pixelSize: 12
                    color: FluTheme.fontTertiaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                    Layout.maximumWidth: 560
                    Layout.alignment: Qt.AlignHCenter
                }
                Item { Layout.fillHeight: true }
            }
        }

        // ---- 页 1：路径 + 选项 ----
        Item {
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                Text {
                    text: "选择安装位置"
                    font.pixelSize: 20
                    font.bold: true
                    color: FluTheme.fontPrimaryColor
                }
                Text {
                    text: "请选择程序安装目录："
                    font.pixelSize: 13
                    color: FluTheme.fontSecondaryColor
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    FluTextBox {
                        id: pathBox
                        Layout.fillWidth: true
                        text: Installer.installDir
                        placeholderText: "安装目录"
                    }
                    FluButton {
                        text: "浏览..."
                        onClicked: {
                            var dir = Installer.browseDirectory(pathBox.text)
                            if (dir) {
                                pathBox.text = dir
                            }
                        }
                    }
                }
                Item { height: 2 }
                FluCheckBox {
                    id: shortcutBox
                    text: "创建桌面快捷方式"
                    checked: true
                }
                FluCheckBox {
                    id: launchBox
                    text: "安装完成后立即启动"
                    checked: true
                }
                Item { Layout.fillHeight: true }
                Text {
                    text: "已有同名文件时将覆盖更新程序文件。"
                    font.pixelSize: 12
                    color: FluTheme.fontTertiaryColor
                }
            }
        }

        // ---- 页 2：进度 ----
        Item {
            ColumnLayout {
                anchors.centerIn: parent
                width: 520
                spacing: 16
                Text {
                    text: "正在安装"
                    font.pixelSize: 20
                    font.bold: true
                    color: FluTheme.fontPrimaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Text {
                    text: window.statusText
                    font.pixelSize: 13
                    color: FluTheme.fontSecondaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }
                FluProgressBar {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 8
                    Layout.topMargin: 4
                    indeterminate: false
                    value: window.progressValue
                    progressVisible: true
                }
                Text {
                    text: Math.round(window.progressValue) + " %"
                    font.pixelSize: 12
                    color: FluTheme.fontTertiaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
            }
        }

        // ---- 页 3：完成 ----
        Item {
            ColumnLayout {
                anchors.centerIn: parent
                width: 560
                spacing: 10
                Item {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: 64
                    Layout.preferredHeight: 64 * 9 / 16
                    Image {
                        id: doneIcon
                        anchors.fill: parent
                        source: "res/icon.svg"
                        sourceSize: Qt.size(width, height)
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        visible: false
                    }
                    ColorOverlay {
                        anchors.fill: doneIcon
                        source: doneIcon
                        color: FluTheme.primaryColor
                    }
                }
                Text {
                    text: "安装完成"
                    font.pixelSize: 22
                    font.bold: true
                    color: FluTheme.fontPrimaryColor
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Text {
                    text: "有声书下载器 已成功安装到：\n" + window.installDir
                    font.pixelSize: 13
                    color: FluTheme.fontSecondaryColor
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }
                FluCheckBox {
                    id: launchFinal
                    text: "立即启动程序"
                    checked: window.launchAfter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    // 底部按钮栏
    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 16
        spacing: 8
        Item { Layout.fillWidth: true }
        FluButton {
            id: backButton
            text: "上一步"
            visible: window.currentPage === 1
            onClicked: {
                window.currentPage -= 1
            }
        }
        FluButton {
            id: cancelButton
            text: "取消"
            visible: window.currentPage < 2
            onClicked: {
                window.close()
            }
        }
        FluButton {
            id: nextButton
            text: window.currentPage === 3 ? "完成" : "下一步"
            onClicked: {
                if (window.currentPage === 0) {
                    window.currentPage = 1
                } else if (window.currentPage === 1) {
                    var dir = pathBox.text.trim()
                    if (!dir) {
                        Installer.showMessage("请选择安装目录。")
                        return
                    }
                    window.installDir = dir
                    window.makeShortcut = shortcutBox.checked
                    window.launchAfter = launchBox.checked
                    window.currentPage = 2
                    nextButton.enabled = false
                    cancelButton.enabled = false
                    Installer.startInstall(dir, shortcutBox.checked)
                } else if (window.currentPage === 3) {
                    if (launchFinal.checked) {
                        Installer.launchApp()
                    }
                    window.close()
                }
            }
        }
    }
}