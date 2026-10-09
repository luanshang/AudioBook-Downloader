pragma Singleton

import QtQuick 2.15
import FluentUI 1.0

FluObject {
    id: nav_items

    property var navigationView

    // ============ 上方三个平台页面 ============
    FluPaneItem {
        title: qsTr("懒人听书")
        icon: FluentIcons.MusicNote
        iconDelegate: Component {
            Image {
                width: 24
                height: 24
                source: "qrc:/qml/res/platform-lrts.svg"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                sourceSize.width: 96
                sourceSize.height: 96
            }
        }
        url: "qrc:/qml/page/PageLRTS.qml"
        onTap: navigationView.push(url)
    }

    FluPaneItem {
        title: qsTr("喜马拉雅")
        icon: FluentIcons.Microphone
        iconDelegate: Component {
            Image {
                width: 24
                height: 24
                source: "qrc:/qml/res/platform-ximalaya.svg"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                sourceSize.width: 96
                sourceSize.height: 96
            }
        }
        url: "qrc:/qml/page/PageXimalaya.qml"
        onTap: navigationView.push(url)
    }

    FluPaneItem {
        title: qsTr("起点")
        icon: FluentIcons.ReadingMode
        iconDelegate: Component {
            Image {
                width: 24
                height: 24
                source: "qrc:/qml/res/platform-qidian.svg"
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                sourceSize.width: 96
                sourceSize.height: 96
            }
        }
        url: "qrc:/qml/page/PageQidian.qml"
        onTap: navigationView.push(url)
    }
}
