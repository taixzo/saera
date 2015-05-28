/*
  Copyright (C) 2013 Jolla Ltd.
  Contact: Thomas Perl <thomas.perl@jollamobile.com>
  All rights reserved.

  You may use this file under the terms of BSD license as follows:

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the Jolla Ltd nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR
  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

import QtQuick 2.0
import QtMultimedia 5.0
import Sailfish.Silica 1.0
import io.thp.pyotherside 1.0
import QtPositioning 5.2


Page {
    id: page


    function speak() {
      mainWindow.activate()
      playSound.play()
      busyIndicator.running = true;
      py.call('saera2.run_voice',[],function(res) {
        listModel.append({value: res, who: "me", link: false});
        py.call('saera2.run_text', [res], function(result){
            busyIndicator.running = false;
            if (typeof(result)=="string") {
              listModel.append({value: result, who: "saera", link: false});
            } else {
              for (var i in result) {
                listModel.append({value: result[i][0], who: "saera", link: result[i][1]});
              }
            }
            // messages.scrollToBottom();
        });
        // messages.scrollToBottom();
      })
    }

    function activate_morning() {
      if (applicationActive) {
        py.call('saera2.resume_daemons',[],function(result){})
        py.call('saera2.activate',[],function(result){
          busyIndicator.running = false;
            if (typeof(result)=="string") {
              if (result != "") {
                listModel.append({value: result, who: "saera", link: false});
              }
            } else {
              for (var i in result) {
                listModel.append({value: result[i][0], who: "saera", link: result[i][1]});
              }
            }
        })
      } else {
        py.call('saera2.pause_daemons',[],function(result){})
      }
    }

    function load_msg(msg) {
        loadingText.text = msg
    }

    Component.onCompleted: {
      mainWindow.selectedCountChanged.connect(page.speak)
      mainWindow.textSelectedCountChanged.connect(inputfield.forceActiveFocus)
      mainWindow.onApplicationActiveChanged.connect(page.activate_morning)
      messages.visible = false
      inputfield.visible = false
      btn.visible = false
    }

    Component.onDestruction: {
      py.call('saera2.quit', [],function(result){})
    }

    Python {
         id:py
         Component.onCompleted: {

                 addImportPath(Qt.resolvedUrl('.').substr('file://'.length));
//             addImportPath('/opt/sdk/saera/usr/share/saera/qml/pages');

             importModule('saera2', function() {
                call('saera2.initialize', [], function(result){
                  btn.icon.source = "image://theme/icon-m-mic"
                  messages.visible = true
                  inputfield.visible = true
                  btn.visible = true
                  loadingIndicator.running = false
                  loadingText.visible = false
                  call('saera2.set_position', [src.position.coordinate.latitude, src.position.coordinate.longitude], function (result){})
                  src.canCallPython = true
                  page.activate_morning()
                });
             });
             setHandler('start',page.speak)
             setHandler('load_msg', page.load_msg)
         }
         onError: console.log('Python error: ' + traceback)
    }

    SilicaListView {

        id: messages
        VerticalScrollDecorator {
            flickable: messages
        }
        anchors.top: parent.top
        anchors.bottom: btn.top
        // anchors.bottomMargin: Theme.paddingLarge
        anchors.bottomMargin: 100

        width: parent.width
//        height: parent.height

        model: ListModel {
            id: listModel
            ListElement { value: "How can I help you?"; who: "saera" }
        }
        delegate: Item {
            width: ListView.view.width

            Text {
                id: t
                anchors {
                    left: parent.left
                    right: parent.right
                    margins: Theme.paddingLarge
                }
                text: value
                wrapMode: Text.Wrap
                width: parent.width - 2 * Theme.paddingLarge
                horizontalAlignment: who=="me" ? Text.AlignRight : Text.AlignLeft
                color: who=="me" ? Theme.secondaryHighlightColor : Theme.highlightColor
                // backgroundColor: link ? Theme.BackgroundColorA : undefined
            }
            height: t.lineCount*(t.font.pixelSize-1) + Theme.itemSizeSmall

            Component.onCompleted: {
                messages.scrollToBottom()
            }
        }
    }


    TextField {
        // anchors.top: messages.bottom
        anchors.bottom: parent.bottom
        id: inputfield
        width: parent.width
        label: "Text field"
        placeholderText: "Type here"
        EnterKey.onClicked: {
            parent.focus = true;
            busyIndicator.running = true;
            listModel.append({value: text, who: "me", link: false})
            py.call('saera2.run_text', [text], function(result){
                busyIndicator.running = false;
                if (typeof(result)=="string") {
                  listModel.append({value: result, who: "saera", link: false});
                } else {
                  for (var i in result) {
                    listModel.append({value: result[i][0], who: "saera", link: result[i][1]});
                  }
                }
                // messages.scrollToBottom();
            });
            text = "";
        }
    }

    SoundEffect {
        id: playSound
        source: "resources/Slick.wav"
    }

    IconButton {
        id: btn
        anchors.bottom: inputfield.top
        anchors.horizontalCenter: parent.horizontalCenter
        // icon.source: "image://theme/icon-m-mic"
        icon.source: "image://theme/icon-l-mute-mic"
        onClicked: {
          speak()
        }
    }

    BusyIndicator {
      id: busyIndicator
      anchors.centerIn: btn
      running: false
      color: Theme.primaryColor
      size: BusyIndicatorSize.Large
    }

    BusyIndicator {
      id: loadingIndicator
      anchors.centerIn: page
      running: true
      color: Theme.primaryColor
      size: BusyIndicatorSize.Large

    }
    Text {
      id: loadingText
      anchors.top: loadingIndicator.bottom
      anchors.horizontalCenter: loadingIndicator.horizontalCenter
      text: "Loading"
      color: Theme.highlightColor
    }

    PositionSource {
        id: src
        updateInterval: 60000
        active: true
        property bool canCallPython: false

        onPositionChanged: {
            var coord = src.position.coordinate;
            if (canCallPython) {
                py.call('saera2.set_position', [coord.latitude, coord.longitude], function (result){})
            }
            console.log("Coordinate:", coord.longitude, coord.latitude);
        }
    }
}
