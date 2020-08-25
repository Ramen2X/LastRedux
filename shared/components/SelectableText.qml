import QtQuick 2.15

TextEdit {
  id: root

  color: '#FFF'
  readOnly: true
  renderType: Text.NativeRendering
  selectByMouse: true
  selectionColor: Qt.rgba(255, 255, 255, 0.15)
  wrapMode: Text.Wrap

  // Match style of standard label
  font {
    letterSpacing: 0.25
    weight: Font.Medium
  }

  HoverHandler {
    id: hoverHandler
    
    cursorShape: Qt.IBeamCursor // Show correct cursor when hovering over text
  }

  PointHandler {
    id: pointHandler

    acceptedButtons: Qt.RightButton
    
    onActiveChanged: {
      if (active) {
        contextMenu.open()
      }
    }
  }

  // Add context menu to copy the content
  TextContextMenu {
    id: contextMenu

    text: root
  }
}