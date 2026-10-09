pragma Singleton

import QtQuick 2.15
import FluentUI 1.0

FluObject {
    id: nav_footer

    property var navigationView

    FluPaneItem {
        title: qsTr("设置")
        iconDelegate: Component {
            Image {
                width: 18
                height: 18
                source: "qrc:/qml/res/settings.svg"
                fillMode: Image.PreserveAspectFit
            }
        }
        url: "qrc:/qml/page/PageSettings.qml"
        onTap: navigationView.push(url)
    }
}
