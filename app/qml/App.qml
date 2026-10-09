import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0

FluLauncher {
    id: app

    Connections {
        target: FluApp
        function onUseSystemAppBarChanged() {
            Settings.saveUseSystemAppBar(FluApp.useSystemAppBar)
        }
    }

    // 明暗主题切换：跟随系统 / 手动切换，带过渡动画
    Connections {
        target: FluTheme
        function onDarkModeChanged() {
            // 持久化当前主题（0=跟随系统 1=亮 2=暗）
            AppBridge.saveDarkMode(FluTheme.darkMode)
        }
    }

    Component.onCompleted: {
        FluApp.init(app, Qt.locale("zh_CN"))
        FluApp.windowIcon = "qrc:/qml/res/favicon.ico"
        FluApp.useSystemAppBar = false

        // 主题切换动画由 MainWindow 的全窗遮罩统一处理。
        FluTheme.animationEnabled = false

        FluRouter.routes = {
            "/": "qrc:/qml/window/MainWindow.qml",
        }
        FluRouter.navigate("/")
    }
}
