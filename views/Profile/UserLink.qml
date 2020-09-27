import QtQuick 2.14

import '../../shared/components'

Item {
  id: root

  property var address
  property alias imageSource: avatar.source
  property alias username: usernameLabel.text
  property alias fullName: realNameLabel.text

  opacity: hoverHandler.hovered && pointHandler.active ? 0.5 : 1

  height: avatar.height

  HoverHandler {
    id: hoverHandler
  }

  // TODO: Add context menu
  PointHandler {
    id: pointHandler

    enabled: !!address
  }
  
  TapHandler {
    acceptedButtons: Qt.LeftButton

    onTapped: {
      if (root.address) {
        Qt.openUrlExternally(root.address)
      }
    }
  }

  // --- Avatar ---

  Picture {
    id: avatar

    type: kArtist // TODO: Add user type

    anchors {
      top: parent.top
      left: parent.left

      leftMargin: 15
    }
  }

  // --- Username ---

  Label {
    id: usernameLabel

    elide: Text.ElideRight
    style: kTitleSecondary

    anchors {
      top: parent.top
      right: parent.right
      left: avatar.right

      rightMargin: 15
      leftMargin: 10
    }
  }

  // --- Real Name ---

  Label {
    id: realNameLabel

    elide: Text.ElideRight
    opacity: 0.81
    style: kBodyPrimary

    anchors {
      top: usernameLabel.bottom
      right: parent.right
      left: avatar.right

      topMargin: 2
      rightMargin: 15
      leftMargin: 10
    }
  }
}