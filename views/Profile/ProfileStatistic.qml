import QtQuick 2.14

import '../../shared/components'
import '../../util/helpers.js' as Helpers

Item {
  property string iconName
  property var value
  property string caption
  
  height: iconContainer.height

  // --- Icon ---

  Item {
    id: iconContainer

    width: 18
    height: width

    Image {
      source: `../../shared/resources/icons/small/${iconName}.png`

      anchors.centerIn: parent
    }

    anchors {
      top: parent.top
      left: parent.left
    }
  }

  // --- Value and Caption ---

  Label {
    id: label
    
    elide: Text.ElideRight
    style: kCaption
    text: value ? `${Helpers.numberWithCommas(value)} ${caption}` : ''

    anchors {
      verticalCenter: iconContainer.verticalCenter

      right: parent.right
      left: iconContainer.right

      leftMargin: 10
    }

    // --- Placeholder ---

    Rectangle {
      opacity: 0.2
      radius: 4
      visible: !value

      height: 16

      anchors {
        verticalCenter: parent.verticalCenter

        right: parent.right
        left: parent.left
      }
    }
  }
}