import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import FluentUI 1.0

FluScrollablePage {
    id: page
    title: qsTr("版权与免责声明")

    ColumnLayout {
        width: parent.width
        spacing: 12

        FluText {
            text: qsTr("版权与免责声明")
            font: FluTextStyle.Title
        }

        FluText {
            text: qsTr("请在使用下载、播放及相关功能前仔细阅读。使用本软件即表示你理解并同意以下内容。")
            color: FluTheme.fontSecondaryColor
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        TextArea {
            Layout.fillWidth: true
            Layout.preferredHeight: 620
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            text: disclaimerText
            font.pixelSize: 13
            color: FluTheme.dark ? "#e6e6e6" : "#252525"
            background: Rectangle {
                radius: 4
                border.width: 1
                border.color: FluTheme.dark ? "#555555" : "#d0d0d0"
                color: FluTheme.dark ? "#1e1e1e" : "#fafafa"
            }
        }
    }

    property string disclaimerText: qsTr("一、用户责任声明\n用户在使用本软件进行下载等操作时，需自行承担因自身行为而直接或间接引发的一切民事或刑事法律责任。此类责任涵盖但不限于侵权赔偿责任、因违反法律法规而产生的罚款责任，以及因传播非法内容所导致的法律后果等。特别需要强调的是，若用户故意利用本软件下载受版权保护且明确禁止下载的内容，并用于商业盈利、恶意传播等侵权行为，除需承担民事赔偿外，还可能面临刑事诉讼及侵犯著作权罪相关法律责任。\n\n" +
        "二、版权声明\n（1）本软件所涉及的下载资料（包括但不限于文字、数据、图片、图表、照片、软件、音像），其版权完全归原所有者所有。未经版权所有者书面许可，用户不得对下载资料进行修改、复制、分发、传播、展示或嵌入其他作品等操作，否则将构成侵权行为。\n（2）若本软件部分内容涉及开源协议，将在相关文档中另行说明开源内容的版权和使用条件，用户应仔细阅读并遵守。\n\n" +
        "三、损害免责声明\n本软件对任何直接、间接、偶然、特殊及继起的损害不承担责任，包括因不正当使用网络服务、网络交易、用户传送的信息变动，或链接网站提供的资料和服务的合法性、完整性、时效性等引发的损害。用户不得利用软件漏洞攻击服务器、传播恶意软件或垃圾邮件。\n\n" +
        "四、担保免责声明\n本软件不提供任何明示或默示担保，不保证服务满足用户要求、持续不中断、及时、安全或无错误。用户通过本软件取得的信息资料的可信性由用户自行判断，并自行承担系统受损或资料丢失的风险。\n\n" +
        "五、特定情况免责细则\n（1）因用户泄露密码、共享账号导致的个人资料泄露，本软件不承担责任，用户应定期更改密码并设置强密码。\n（2）因计算机问题、黑客攻击、病毒、政府管制等不可抗力导致的资料泄露、丢失、盗用或篡改，本软件将尽力保护用户资料，但无法对不可抗力后果完全负责。\n（3）因第三方网站造成的资料泄露、法律争议，以及使用第三方内容、信息和服务受到的侵害，本软件不承担责任。\n\n" +
        "六、版权问题与使用限制\n因使用本软件产生的版权问题由使用者自行负责。本软件提供的内容仅可在合法合规前提下用于学习交流，禁止未经授权用于教学培训收费等商业活动。若发现软件内有侵犯版权的内容，请及时向软件开发者反馈。\n\n" +
        "七、下载后处理与支持原创倡议\n（1）请用户在下载内容后的24小时内删除。软件可能采取合法合规的技术手段检查用户是否遵守此规定，发现违规时可能限制使用。\n（2）为尊重作者版权，请前往资源原始发布网站观看或收听以支持原创，并通过合法打赏、推荐等方式支持作者。")
}
