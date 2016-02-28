import QtQuick 1.1
import com.nokia.meego 1.0
import com.thpinfo.python 1.0


Page {
    id: mainPage
    Rectangle {
        anchors.fill: parent
        color: "#000000"

        Column {
          width: parent.width
          height: parent.height
          spacing: Theme.paddingMedium
                
          // PageHeader {
          //   id: header
          //   title: "Settings"
          // }
          Row {
            width: parent.width
            spacing: parent.spacing
            x: parent.spacing

            Button {
                text: "Back"
                onClicked: {
                    pageStack.pop()
                }
            }
          }

          Row {
            width: parent.width
            spacing: parent.spacing
            x: parent.spacing

            Label {
              width: parent.width - (3 * parent.spacing)
              text: "Device key:"
              color: "#FFFFFF"
              font.pixelSize: 24
            }
          }
          Row {
            width: parent.width
            spacing: parent.spacing
            x: parent.spacing

            Label {
              width: parent.width - (3 * parent.spacing)
              horizontalAlignment: Text.AlignHCenter
              
              text: "0XfQ"
              color: "#FFFFFF"
              font.pixelSize: 24*6
            }
          }
          Row {
            width: parent.width
            spacing: parent.spacing
            x: parent.spacing

            Label {
              width: parent.width - (3 * parent.spacing)
              text: "Enter key to connect to:"
              color: "#FFFFFF"
              font.pixelSize: 24
            }
          }
          Row {
            width: parent.width
            spacing: parent.spacing
            x: parent.spacing

            TextField {
              width: parent.width
              // horizontalAlignment: Text.AlignHCenter
              placeholderText: "----"
              font.pixelSize: 24
            }
          }
        }
    }
}