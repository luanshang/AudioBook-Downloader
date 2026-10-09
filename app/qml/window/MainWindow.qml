import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0
import "../global"

FluWindow {
    id: window
    title: "有声书下载器 v2.0"
    width: 1100
    height: 720
    minimumWidth: 900
    minimumHeight: 560
    launchMode: FluWindowType.SingleTask
    fitsAppBarWindows: true

    appBar: FluAppBar {
        width: window.width
        height: 30
        // 明暗主题切换按钮（带 FluentUI 过渡动画）
        showDark: true
        icon: "qrc:/qml/res/favicon.ico"
        // 点击切换时持久化主题选择
        darkClickListener: function(btn) {
            var next = FluTheme.darkMode === FluThemeType.DarkMode.Dark
                ? FluThemeType.DarkMode.Light : FluThemeType.DarkMode.Dark
            FluTheme.darkMode = next
            AppBridge.saveDarkMode(next)
        }
    }

    property bool previousThemeDark: FluTheme.dark

    Connections {
        target: FluTheme
        function onDarkModeChanged() {
            themeTransition.color = window.previousThemeDark ? "#202020" : "#F3F3F3"
            window.previousThemeDark = FluTheme.dark
            themeTransition.opacity = 0.92
            themeFade.restart()
        }
    }

    Rectangle {
        id: themeTransition
        anchors.fill: parent
        z: 10000
        opacity: 0
        visible: opacity > 0
        enabled: false

        NumberAnimation {
            id: themeFade
            target: themeTransition
            property: "opacity"
            from: 0.92
            to: 0
            duration: 320
            easing.type: Easing.OutCubic
        }
    }

    property bool sidebarCollapsed: true
    property bool autoHideSidebar: false

    Item {
        id: sidebarControls
        z: 9000
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.topMargin: 36
        width: 86
        height: 34

        Row {
            anchors.fill: parent
            spacing: 2
            visible: !autoHideSidebar || sidebarHover.containsMouse

            FluIconButton {
                id: btnCollapse
                width: 34
                height: 34
                iconSize: 16
                iconSource: sidebarCollapsed ? FluentIcons.ChevronRight : FluentIcons.ChevronLeft
                onClicked: {
                    autoHideSidebar = false
                    sidebarCollapsed = !sidebarCollapsed
                }
            }

            FluIconButton {
                id: btnAutoHide
                width: 34
                height: 34
                iconSize: 16
                iconSource: autoHideSidebar ? FluentIcons.Lock : FluentIcons.Unlock
                onClicked: autoHideSidebar = !autoHideSidebar
            }
        }
    }

    MouseArea {
        id: sidebarHover
        z: 8999
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 86
        hoverEnabled: true
        visible: autoHideSidebar
    }

    FluContentDialog {
        id: disclaimerDialog
        title: qsTr("版权与免责声明")
        message: qsTr("本软件仅提供网络资料检索、播放和下载工具。用户必须确保所有操作及下载内容合法合规，并自行承担因侵权、传播、商业使用、账号共享、第三方网站或网络服务引发的全部责任。下载内容仅限合法的学习交流用途，请尊重作者版权并支持原创。完整条款可在设置页面的“版权与免责声明”中查看。使用本软件即表示你已阅读并同意相关声明。")
        positiveText: qsTr("我已阅读并同意")
        negativeText: qsTr("退出")
        onPositiveClicked: AppBridge.acknowledge_disclaimer()
        onNegativeClicked: Qt.quit()
    }

    FluNavigationView {
        id: nav_view
        width: parent.width
        height: parent.height
        displayMode: autoHideSidebar
            ? (sidebarHover.containsMouse ? FluNavigationViewType.Open : FluNavigationViewType.Compact)
            : (sidebarCollapsed ? FluNavigationViewType.Compact : FluNavigationViewType.Open)
        pageMode: FluNavigationViewType.NoStack

        // 顶部页面：懒人听书 / 喜马拉雅 / 起点
        items: NavItems

        // 底部：设置
        footerItems: NavFooter

        topPadding: window.useSystemAppBar ? 0 : 30

        Component.onCompleted: {
            buttonBack.visible = false
            NavItems.navigationView = nav_view
            NavFooter.navigationView = nav_view
            initialPageTimer.start()
        }

        Timer {
            id: initialPageTimer
            interval: 120
            repeat: false
            onTriggered: {
                // 等待 items/model 完成后再触发首个页面，避免 currentIndex 为 -1。
                nav_view.setCurrentIndex(0)
                nav_view.push("qrc:/qml/page/PageLRTS.qml")
            }
        }
    }
}
