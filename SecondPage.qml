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
import Sailfish.Silica 1.0
import io.thp.pyotherside 1.0


Page {
  id: page2

  property Python py
  property variant settings

  SilicaFlickable {
    anchors.fill: parent
    Column {
      width: parent.width
      height: parent.height
      spacing: Theme.paddingMedium
            
      PageHeader {
        id: header
        title: "Settings"
      }
      /*Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        Label {
          width: parent.width - (3 * parent.spacing)
          text: "Device key:"
          font.pixelSize: Theme.fontSizeLarge
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
          font.pixelSize: Theme.fontSizeLarge*6
        }
      }
      Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        Label {
          width: parent.width - (3 * parent.spacing)
          text: "Enter key to connect to:"
          font.pixelSize: Theme.fontSizeLarge
        }
      }
      Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        TextField {
          width: parent.width
          horizontalAlignment: Text.AlignHCenter
          placeholderText: "----"
          font.pixelSize: Theme.fontSizeLarge
        }
      }*/
      Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        TextSwitch {
            id: modeSwitch
            text: "Enable 24-hour mode"
            description: "Currently in 12 hour mode"
            onCheckedChanged: {
                console.log(checked ? "Checked" : "Unchecked")
                modeSwitch.description = "Currently in " + (checked ? "24" : "12") + " hour mode"
                py.call('saera2.set_24_hour_mode', [checked], function(res){})
            }
        }
      }
      Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        ComboBox {
          // width: 
          label: "Online voice recognition"
          id: ovr_mode

          currentIndex: page2.settings.internet_voice

          menu: ContextMenu {
            MenuItem { text: "Off"}
            MenuItem { text: "Wifi only" }
            MenuItem { text: "Always" }
          }
          onCurrentIndexChanged: {
            console.log(ovr_mode.value)
            py.call('saera2.set_ovr_mode', [ovr_mode.value], function(res){})
          }
        }
      }

      Row {
        width: parent.width
        spacing: parent.spacing
        x: parent.spacing

        visible: ovr_mode.value != "Off"

        ComboBox {
          label: "Engine to use"
          id: ovr_engine

          menu: ContextMenu {
            MenuItem { text: "Wit" }
            MenuItem {
              text: "Houndify"
              enabled: false
            }
          }
        }

      }
    }
  }
}





