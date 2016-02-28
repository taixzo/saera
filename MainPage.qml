import QtQuick 1.1
import com.nokia.meego 1.0
import com.thpinfo.python 1.0

PageStack {
    id: pageStack
    
    Component.onCompleted: {
        pageStack.push(Qt.resolvedUrl("harmattan/FirstPage.qml"))
    }
}