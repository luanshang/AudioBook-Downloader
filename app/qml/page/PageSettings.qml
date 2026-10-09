import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0
import "../global"

FluScrollablePage {
    id: page
    title: qsTr("设置")
    property int selectedCategory: 0

    RowLayout {
        width: parent.width
        height: 620
        spacing: 16

        Rectangle {
            Layout.preferredWidth: 190
            Layout.fillHeight: true
            radius: 6
            color: FluTheme.dark ? Qt.rgba(0, 0, 0, 0.10) : Qt.rgba(1, 1, 1, 0.60)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 6

                Rectangle {
                    id: generalCategory
                    Layout.fillWidth: true
                    height: 38
                    radius: 5
                    color: page.selectedCategory === 0
                        ? (FluTheme.dark ? Qt.rgba(0.20, 0.42, 0.62, 0.42) : Qt.rgba(0.22, 0.48, 0.78, 0.14))
                        : (generalHover.containsMouse ? (FluTheme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.06)) : "transparent")
                    Behavior on color { ColorAnimation { duration: 140 } }
                    Label { anchors.fill: parent; anchors.leftMargin: 12; verticalAlignment: Text.AlignVCenter; text: qsTr("通用设置") }
                    MouseArea { id: generalHover; anchors.fill: parent; hoverEnabled: true; onClicked: page.selectedCategory = 0 }
                }
                Rectangle {
                    id: disclaimerCategory
                    Layout.fillWidth: true
                    height: 38
                    radius: 5
                    color: page.selectedCategory === 1
                        ? (FluTheme.dark ? Qt.rgba(0.20, 0.42, 0.62, 0.42) : Qt.rgba(0.22, 0.48, 0.78, 0.14))
                        : (disclaimerHover.containsMouse ? (FluTheme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.06)) : "transparent")
                    Behavior on color { ColorAnimation { duration: 140 } }
                    Label { anchors.fill: parent; anchors.leftMargin: 12; verticalAlignment: Text.AlignVCenter; text: qsTr("版权与免责声明") }
                    MouseArea { id: disclaimerHover; anchors.fill: parent; hoverEnabled: true; onClicked: page.selectedCategory = 1 }
                }
                Rectangle {
                    id: aboutCategory
                    Layout.fillWidth: true
                    height: 38
                    radius: 5
                    color: page.selectedCategory === 2
                        ? (FluTheme.dark ? Qt.rgba(0.20, 0.42, 0.62, 0.42) : Qt.rgba(0.22, 0.48, 0.78, 0.14))
                        : (aboutHover.containsMouse ? (FluTheme.dark ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0, 0, 0.06)) : "transparent")
                    Behavior on color { ColorAnimation { duration: 140 } }
                    Label { anchors.fill: parent; anchors.leftMargin: 12; verticalAlignment: Text.AlignVCenter; text: qsTr("关于") }
                    MouseArea { id: aboutHover; anchors.fill: parent; hoverEnabled: true; onClicked: page.selectedCategory = 2 }
                }
                Item { Layout.fillHeight: true }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.rightMargin: 24
            currentIndex: page.selectedCategory

            ColumnLayout {
                spacing: 14
                Label {
                    text: qsTr("通用设置")
                    font: FluTextStyle.Title
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("界面主题"); Layout.preferredWidth: 120 }
                    FluComboBox {
                        id: themeCombo
                        Layout.preferredWidth: 110
                        Layout.maximumWidth: 110
                        model: ["跟随系统", "亮色", "暗色"]
                        currentIndex: {                            var m = AppBridge.loadDarkMode()
                            return m === 1 ? 1 : (m === 2 ? 2 : 0)
                        }
                        onActivated: function(index) {
                            var mode = index === 1 ? FluThemeType.DarkMode.Light
                                : (index === 2 ? FluThemeType.DarkMode.Dark : FluThemeType.DarkMode.System)
                            FluTheme.darkMode = mode
                            AppBridge.saveDarkMode(mode)
                            themeStatus.text = qsTr("主题已更新")
                        }
                    }
                    Label { id: themeStatus; color: FluTheme.fontSecondaryColor }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Label { text: qsTr("默认保存目录"); Layout.preferredWidth: 120 }
                    FluTextBox {
                        id: saveDirBox
                        Layout.fillWidth: true
                        text: Settings.saveDir || ""
                    }
                    FluButton {
                        text: qsTr("浏览")
                        onClicked: Bridge.choose_directory()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    FluButton {
                        text: qsTr("保存设置")
                        onClicked: {
                            Settings.saveDir = saveDirBox.text
                            statusLabel.text = qsTr("设置已保存")
                        }
                    }
                    FluButton {
                        text: qsTr("打开日志目录")
                        onClicked: Bridge.open_log_dir()
                    }
                    Item { Layout.fillWidth: true }
                    Label { id: statusLabel; color: FluTheme.fontSecondaryColor }
                }

                Item { Layout.fillHeight: true }
            }

            ColumnLayout {
                spacing: 10
                Label {
                    text: qsTr("版权与免责声明")
                    font: FluTextStyle.Title
                }
                Label {
                    text: AppBridge.load_disclaimer_ack()
                        ? qsTr("首次启动声明：已确认")
                        : qsTr("首次启动声明：尚未确认")
                    color: FluTheme.fontSecondaryColor
                }
                TextArea {
                    id: disclaimerBox
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.Wrap
                    font.pixelSize: 13
                    color: FluTheme.dark ? "#e6e6e6" : "#252525"
                    background: Rectangle {
                        radius: 4
                        border.width: 1
                        border.color: FluTheme.dark ? "#555555" : "#d0d0d0"
                        color: FluTheme.dark ? "#1e1e1e" : "#fafafa"
                    }
                    text: qsTr("一、用户责任声明\n用户在使用本软件进行下载等操作时，需自行承担因自身行为而直接或间接引发的一切民事或刑事法律责任。此类责任涵盖但不限于侵权赔偿责任、因违反法律法规而产生的罚款责任，以及因传播非法内容所导致的法律后果等。特别需要强调的是，若用户故意利用本软件下载受版权保护且明确禁止下载的内容，并用于商业盈利、恶意传播等侵权行为，除需承担民事赔偿外，还可能面临刑事诉讼及侵犯著作权罪相关法律责任。\n\n" +
                        "二、版权声明\n（1）本软件所涉及的下载资料（包括但不限于文字、数据、图片、图表、照片、软件、音像），其版权完全归原所有者所有。未经版权所有者书面许可，用户不得对下载资料进行修改、复制、分发、传播、展示或嵌入其他作品等操作，否则将构成侵权行为。\n（2）若本软件部分内容涉及开源协议，将在相关文档中另行说明开源内容的版权和使用条件，用户应仔细阅读并遵守。\n\n" +
                        "三、损害免责声明\n本软件对任何直接、间接、偶然、特殊及继起的损害不承担责任，包括因不正当使用网络服务、网络交易、用户传送的信息变动，或链接网站提供的资料和服务的合法性、完整性、时效性等引发的损害。用户不得利用软件漏洞攻击服务器、传播恶意软件或垃圾邮件。\n\n" +
                        "四、担保免责声明\n本软件不提供任何明示或默示担保，不保证服务满足用户要求、持续不中断、及时、安全或无错误。用户通过本软件取得的信息资料的可信性由用户自行判断，并自行承担系统受损或资料丢失的风险。\n\n" +
                        "五、特定情况免责细则\n（1）因用户泄露密码、共享账号导致的个人资料泄露，本软件不承担责任，用户应定期更改密码并设置强密码。\n（2）因计算机问题、黑客攻击、病毒、政府管制等不可抗力导致的资料泄露、丢失、盗用或篡改，本软件将尽力保护用户资料，但无法对不可抗力后果完全负责。\n（3）因第三方网站造成的资料泄露、法律争议，以及使用第三方内容、信息和服务受到的侵害，本软件不承担责任。\n\n" +
                        "六、版权问题与使用限制\n因使用本软件产生的版权问题由使用者自行负责。本软件提供的内容仅可在合法合规前提下用于学习交流，禁止未经授权用于教学培训收费等商业活动。若发现软件内有侵犯版权的内容，请及时向软件开发者反馈。\n\n" +
                        "七、下载后处理与支持原创倡议\n（1）请用户在下载内容后的24小时内删除。软件可能采取合法合规的技术手段检查用户是否遵守此规定，发现违规时可能限制使用。\n（2）为尊重作者版权，请前往资源原始发布网站观看或收听以支持原创，并通过合法打赏、推荐等方式支持作者。")
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                }
            }

            ColumnLayout {
                spacing: 16
                RowLayout {
                    Image {
                        source: "qrc:/qml/res/about.svg"
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        fillMode: Image.PreserveAspectFit
                    }
                    Label {
                        text: qsTr("关于")
                        font: FluTextStyle.Title
                    }
                    Item { Layout.fillWidth: true }
                }
                Label {
                    text: qsTr("有声书下载器")
                    font.pixelSize: 22
                    font.bold: true
                }
                Label {
                    text: qsTr("版本 0.0.1")
                    color: FluTheme.fontSecondaryColor
                }
                Label {
                    text: qsTr("基于 PySide6 + FluentUI 的多平台音频工具")
                    color: FluTheme.fontSecondaryColor
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: FluTheme.dark ? "#3a3a3a" : "#e5e5e5"
                }
                Label { text: qsTr("支持平台"); font: FluTextStyle.Subtitle }
                Label {
                    text: qsTr("懒人听书、喜马拉雅、起点")
                    color: FluTheme.fontSecondaryColor
                }
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("本软件仅提供网络资料检索、播放和下载工具。请遵守相关法律法规、平台规则及版权要求，仅在获得合法授权的范围内使用。")
                    color: FluTheme.fontSecondaryColor
                }
                Item { Layout.fillHeight: true }
            }
        }
    }

    Connections {
        target: Bridge
        function onDirectoryChosen(path) {
            saveDirBox.text = path
            Settings.saveDir = path
            statusLabel.text = qsTr("默认保存目录已更新")
        }
        function onMessage(title, content) {
            statusLabel.text = content
        }
    }
}
