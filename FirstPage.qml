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


Page {
    id: page

    function speak() {
      playSound.play()
      py.call('saera2.run_voice',[],function(res) {
        listModel.append({value: res, who: "me"});
        py.call('saera2.run_text', [res], function(result){
            if (typeof(result)=="string") {
              listModel.append({value: result, who: "saera"});
            } else {
              for (var i in result) {
                listModel.append({value: result[i], who: "saera"});
              }
            }
            // messages.scrollToBottom();
        });
        // messages.scrollToBottom();
      })
    }


    Component.onCompleted: {
      mainWindow.selectedCountChanged.connect(page.speak)
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
                call('saera2.initialize', [], function(result){});
             });
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
//            ListElement { value: "Hello Saera"; who: "me" }
//            ListElement { value: "Hello!"; who: "saera" }
//            ListElement { value: "What's the weather like in New York City, do I need an umbrella?"; who: "me" }
//            ListElement { value: "The weather in New York City is heavy rain, and 39°."; who: "saera" }
//            ListElement { value: "What about in Washington?"; who: "me" }
//            ListElement { value: "The weather in Washington is clear, and 50°."; who: "saera" }
//            ListElement { value: "Ok. Wake me tomorrow at nine."; who: "me" }
//            ListElement { value: "Setting alarm for 9:00."; who: "saera" }
//            ListElement { value: "What about in Philadelphia?"; who: "me" }
//            ListElement { value: "The weather in Philadelphia is clear, and 50°."; who: "saera" }
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
            }
            height: Theme.itemSizeSmall + t.lineCount*(t.font.pixelSize-1)

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
            listModel.append({value: text, who: "me"})
            py.call('saera2.run_text', [text], function(result){
                if (typeof(result)=="string") {
                  listModel.append({value: result, who: "saera"});
                } else {
                  for (var i in result) {
                    listModel.append({value: result[i], who: "saera"});
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
        icon.source: "image://theme/icon-m-mic"
        onClicked: {
          speak()
        }
    }
}


