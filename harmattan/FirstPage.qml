import QtQuick 1.1
import com.nokia.meego 1.0
import com.thpinfo.python 1.0
import QtMobility.location 1.1


Page {
    id: mainPage

    property bool doneLoading: false

    orientationLock: PageOrientation.LockPortrait

    Component.onDestruction: {
      py.call('saera2.quit', [])
    }

    Rectangle {

        anchors.fill: parent
        color: "#000000"

        Image {
            anchors.top: parent.top
            anchors.left: parent.left
            source: "file:///opt/Saera/qml/Saera/resources/bg_green.png"
        }

        ListView {
                visible: mainPage.doneLoading

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

                    MouseArea {
                      anchors.fill: parent
                      onClicked: {
                        if (who=="me") {
                          inputfield.text = t.text
                          inputfield.forceActiveFocus()
                        }
                      }
                    }

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
                        font.pixelSize: 24
                        color: who=="me" ? "#cccccc" : "#FFFFFF"
                    }
                    height: t.lineCount*(t.font.pixelSize-1) + 25

                }
            }

        Rectangle{
            visible: mainPage.doneLoading
            id: btn
            anchors.bottom: inputfield.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 16
            height: 64
            width: 64
            color: "transparent"
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
                    timer.interval = 200
                    var result = py.call('harmattan_stub.call_func', ['run_voice'])
                    listModel.append({value:result, who: "me", link: false, image: "", lat:0, lon:0});
                    result = py.call('harmattan_stub.call_func', ['run_text', result])
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
        // BusyIndicator {
        //   id: busyIndicator
        //   anchors.centerIn: btn
        //   running: true
        //   style: BusyIndicatorStyle {
            // indicator: Image {
            //     visible: control.running
            //     source: "icon_mic.png"
            //     RotationAnimation on rotation {
            //         running: control.running
            //         loops: Animation.Infinite
            //         duration: 2000
            //         from: 0; to: 360
            //     }
        //     size: small
        //   }
        // }
        Image {
            property bool is_running: false
            id: busyIndicator
            anchors.centerIn: btn
            width: 128
            height: 128
            // visible: control.running
            visible: is_running
            source: "file:///opt/Saera/qml/Saera/resources/spinner.png"
            // source: "spinner.png"
            RotationAnimation on rotation {
                running: busyIndicator.is_running
                // running: control.running
                loops: Animation.Infinite
                duration: 2000
                from: 0; to: 360
            }
        }

        Image {
            property bool is_running: false
            id: loadingIndicator
            anchors.centerIn: parent
            width: 128
            height: 128
            // visible: control.running
            visible: ! mainPage.doneLoading
            source: "file:///opt/Saera/qml/Saera/resources/spinner.png"
            // source: "spinner.png"
            RotationAnimation on rotation {
                running: ! mainPage.doneLoading
                // running: control.running
                loops: Animation.Infinite
                duration: 2000
                from: 0; to: 360
            }
        }

        Label {
            id: loadingText
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: loadingIndicator.bottom
            visible: ! mainPage.doneLoading
            horizontalAlignment: Text.AlignCenter
            text: "Loading..."
            font.pixelSize: 24
            color: "#FFFFFF"
        }

        Timer {
            id: timer
            interval: 2000
            running: true
            repeat: true
            onTriggered: {
                if (mainPage.doneLoading) {
                    var result = py.call('harmattan_stub.get_latest', [])
                    if (result) {
                        busyIndicator.is_running = false;
                        timer.interval = 2000
                        if (typeof(result)=="string") {
                            listModel.append({value: result, who: "saera", link: false, image: "", lat: 0, lon: 0});
                        } else {
                          for (var i in result) {
                            listModel.append({value: result[i][0], who: "saera", link: result[i][1], image: "", lat: 0, lon: 0});
                          }
                        }
                    }
                } else {
                    var result = py.call('harmattan_stub.try_to_connect', [])
                    if (result) {
                        mainPage.doneLoading = true
                    }
                }
            }
        }

        // TextInput {
        //     anchors.bottom: parent.bottom
        //     id: inputfield
        //     width: parent.width

        //     font.pointSize: 24
        //     color: "#ffffff"
        //     // placeholderText: "Type here"
            
        //     Keys.onReturnPressed: {
        //     // onAccepted: {
        //         console.log("Message:"+text)
        //         parent.focus = true;
        //         busyIndicator.is_running = true;
        //         listModel.append({value: text, who: "me", link: false, image: "", lat: 0, lon: 0})
        //         var result = py.call('saera2.run_text', [text])
        //         console.log("Result:"+result)

        //         busyIndicator.is_running = false;
        //         if (typeof(result)=="string") {
        //             listModel.append({value: result, who: "saera", link: false, image: "", lat: 0, lon: 0});
        //         } else {
        //           for (var i in result) {
        //             listModel.append({value: result[i][0], who: "saera", link: result[i][1], image: "", lat: 0, lon: 0});
        //           }
        //         }
        //         text = "";
        //     }
        // }

        TextField {
            anchors.bottom: parent.bottom
            id: inputfield
            width: parent.width
            placeholderText: "Type here"

            Keys.onReturnPressed: {
                console.log("Message:"+text)
                parent.focus = true;
                busyIndicator.is_running = true;
                listModel.append({value: text, who: "me", link: false, image: "", lat: 0, lon: 0})
                timer.interval = 200
                var result = py.call('harmattan_stub.call_func', ['run_text', text])

                // busyIndicator.is_running = false;
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
        // Button {
        // 	anchors.centerIn: parent
        // 	width: parent.width
        // 	height: 32
        // 	text: "Push me"
        // 	onClicked: {
        // 		pageStack.push(Qt.resolvedUrl('SecondPage.qml'))
        // 	}
        // }

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
                    addImportPath('/opt/Saera/qml/Saera/harmattan')

                    importModule('os');
                    // Simulator
    //                console.log(call('os.listdir', ['qml/Saera']));
                    // Device
                    console.log(call('os.listdir', ['/opt/Saera/qml/Saera']));
                    importModule('harmattan_stub');
                    // py.call('saera2.initialize',[])
                    console.log("Got here")

                }
        }
    }

    PositionSource {
        id: src
        updateInterval: 60000
        active: true
        property bool canCallPython: false

        onPositionChanged: {
            var coord = src.position.coordinate;
            latitude = coord.latitude
            longitude = coord.longitude
            console.log("Latitude: "+latitude+", longitude: "+longitude)
            if (canCallPython) {
                py.call('saera2.set_position', [coord.latitude, coord.longitude], function (result){})
            }
        }
    }
}