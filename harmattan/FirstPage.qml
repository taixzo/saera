import QtQuick 1.1
import com.nokia.meego 1.0
import com.thpinfo.python 1.0


Page {
    id: mainPage
    Rectangle {
        anchors.fill: parent
        color: "#000000"

        ListView {

                id: messages

                anchors.top: parent.top
                anchors.bottom: btn.top
                anchors.bottomMargin: 100
                anchors.topMargin: 20

                highlightFollowsCurrentItem: true

                width: parent.width

                model: ListModel {
                    id: listModel

                    ListElement { value: "How can I help you?"; who: "saera"; link: false; image: ""; lat: 0; lon: 0 }
                }
                onCountChanged: {
                    messages.currentIndex = messages.count - 1
                    if (messages.count>2 && listModel.get(messages.count-2).lat) {
                        listModel.get(messages.count-2).lat = 0
                        listModel.get(messages.count-2).lon = 0
                    }
                }
                delegate: Item {
                    width: ListView.view.width

                    Image {
                        id: i
                        anchors {
                            right: parent.right
                            rightMargin: image ? 10 : 0
                        }
                        source: image ? image : ""
                        width: image ? 64 : 0
                        height: image ? 64 : 0
                    }

                    Label {
                        id: d
                        anchors {
                            right: i.left
                            rightMargin: lat ? 10 : 0
                        }
                        color: "#FFFFFF"
                        text: lat ? dist(lat, lon) : ""
                    }

                    Label {
                        id: t
                        anchors {
                            left: parent.left
                            right: d.left
                            margins: 20
                        }
                        text: value
                        wrapMode: Text.Wrap
                        width: parent.width - 2 * 20
                        horizontalAlignment: who=="me" ? Text.AlignRight : Text.AlignLeft
                        color: who=="me" ? "#999999" : "#FFFFFF"
                    }
                    height: t.lineCount*(t.font.pixelSize-1) + 25

                }
            }

        Rectangle{
            id: btn
            anchors.bottom: inputfield.top
            anchors.horizontalCenter: parent.horizontalCenter
            height: 64
            width: 64
            color: "#000000"
            // text: qsTr("Click here!")
            // iconSource: "image://theme/icon-m-camera-video-record"
            Image {
               anchors.centerIn: parent
               // source: "image://theme/icon-m-camera-video-record"
               source: "icon_mic.png"
               width: 64
               height: 64
               fillMode: Image.PreserveAspectFit
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    busyIndicator.running = true;
                    var result = py.call('saera2.run_voice', [])
                    listModel.append({value:result, who: "me", link: false, image: "", lat:0, lon:0});
                    result = py.call('saera2.run_text', [result])
                    busyIndicator.running = false;
                    if (typeof(result)=="string") {
                        listModel.append({value: result, who: "saera", link: false, image: "", lat: 0, lon: 0});
                    } else {
                      for (var i in result) {
                        listModel.append({value: result[i][0], who: "saera", link: result[i][1], image: "", lat: 0, lon: 0});
                      }
                    }
                    // label.visible = true
                    // label.text = py.call('saera2.initialize',[3])
                }
            }
        }
        BusyIndicator {
          id: busyIndicator
          anchors.centerIn: btn
          running: true
        }

        TextField {
            anchors.bottom: parent.bottom
            id: inputfield
            width: parent.width
            placeholderText: "Type here"
            Keys.onReturnPressed: {
                console.log("Message:"+text)
                parent.focus = true;
                busyIndicator.running = true;
                listModel.append({value: text, who: "me", link: false, image: "", lat: 0, lon: 0})
                var result = py.call('saera2.run_text', [text])

                busyIndicator.running = false;
                if (typeof(result)=="string") {
                    listModel.append({value: result, who: "saera", link: false, image: "", lat: 0, lon: 0});
                } else {
                  for (var i in result) {
                    listModel.append({value: result[i][0], who: "saera", link: result[i][1], image: "", lat: 0, lon: 0});
                  }
                }
                text = "";
            }
        }
        Button {
        	anchors.centerIn: parent
        	width: parent.width
        	height: 32
        	text: "Push me"
        	onClicked: {
        		pageStack.push(Qt.resolvedUrl('SecondPage.qml'))
        	}
        }

        Python {
                id: py

                function chdir(newpath) {
                    // Append new path to current path, then use Python to calculate the
                    // real path from it (resolves e.g. '..' to parent directory)
                    path = call('os.path.join', [path, newpath]);
                    path = call('os.path.abspath', [path]);

                    // Replace list model data with list-of-dicts from Python
                    listModel.fill(call('pyotherside.demo', [path]));
                }

                Component.onCompleted: {
                    // Simulator
    //                addImportPath('qml/Saera');
                    // Device
                    addImportPath('/opt/Saera/qml/Saera')

                    importModule('os');
                    // Simulator
    //                console.log(call('os.listdir', ['qml/Saera']));
                    // Device
                    console.log(call('os.listdir', ['/opt/Saera/qml/Saera']));
                    importModule('saera2');
                    py.call('saera2.initialize',[])
                    console.log("Got here")

                }
        }
    }
}