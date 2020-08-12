import QtQuick 2.14

import Kale 1.0

import 'ScrobbleDetails'
import '../shared/components'

Item {
  property ScrobbleDetailsViewModel viewModel

  property bool canDisplayScrobble: {
    // Don't do just viewModel && viewModel.scrobbleData because we need to return a bool value instead of an undefined viewModel.scrobbleData
    if (viewModel && viewModel.scrobbleData) {
      return true
    }

    return false
  }

  property bool canDisplayEntireScrobble: canDisplayScrobble && viewModel.scrobbleData.is_additional_data_downloaded

  // No song playing page
  Item {
    visible: !canDisplayScrobble

    anchors.fill: parent

    Label {
      opacity: 0.5
      style: kTitleSecondary
      
      text: 'No Scrobble Selected'

      anchors.centerIn: parent
    }
  }

  // Song info page
  Item {
    visible: canDisplayScrobble

    anchors.fill: parent
    
    Flickable {
      id: scrollArea
      
      contentHeight: column.height

      anchors.fill: parent

      Column {
        id: column

        width: scrollArea.width

        TrackDetails {
          trackName: canDisplayScrobble && viewModel.scrobbleData.name
          trackLastFmUrl: canDisplayEntireScrobble && viewModel.scrobbleData.lastfm_url
          trackPlays: canDisplayEntireScrobble ? viewModel.scrobbleData.plays : undefined

          artistName: canDisplayScrobble && viewModel.scrobbleData.artist.name
          artistLastFmUrl: canDisplayEntireScrobble && viewModel.scrobbleData.artist.lastfm_url

          albumName: canDisplayScrobble && viewModel.scrobbleData.album.name
          albumLastFmUrl: canDisplayEntireScrobble && viewModel.scrobbleData.album.lastfm_url

          albumImageUrl: {
            if (canDisplayEntireScrobble) {
              return viewModel.scrobbleData.album.image_url
            }
            
            return ''
          }

          width: column.width
        }

        // Artist details
        Item {
          id: artistDetails

          width: column.width
          height: artistDetailsContent.y + artistDetailsContent.height + 30

          Picture {
            id: artistAvatar

            type: kArtist

            source: {
              if (canDisplayEntireScrobble) {
                return viewModel.scrobbleData.artist.image_url
              }

              return ''
            }

            width: 106
            height: width

            anchors {
              top: parent.top
              left: parent.left

              margins: 30
            }
          }

          Column {
            id: artistDetailsContent

            spacing: 15

            anchors {
              top: artistAvatar.top
              right: parent.right
              left: artistAvatar.right

              topMargin: 10
              rightMargin: 30
              leftMargin: 20
            }

            Link {
              elide: Text.ElideRight
              style: kTitlePrimary
              text: canDisplayScrobble && viewModel.scrobbleData.artist.name
              address: canDisplayEntireScrobble && viewModel.scrobbleData.artist.lastfm_url

              width: parent.width
            }

            Row {
              id: row

              property int columnSpacing: 3

              spacing: 20
              visible: canDisplayEntireScrobble

              Column {
                spacing: row.columnSpacing

                Label {
                  style: kNumber
                  text: canDisplayEntireScrobble ? viewModel.scrobbleData.artist.global_listeners : ''
                }

                Label {
                  style: kTitleTertiary
                  text: 'Listeners'
                }
              }

              Column {
                spacing: row.columnSpacing
                
                Label {
                  style: kNumber
                  text: canDisplayEntireScrobble ? viewModel.scrobbleData.artist.global_plays : ''
                }

                Label {
                  style: kTitleTertiary
                  text: 'Plays'
                }
              }

              Column {
                spacing: row.columnSpacing
                
                Label {
                  style: kNumber
                  text: canDisplayEntireScrobble ? viewModel.scrobbleData.artist.plays : ''
                }

                Label {
                  style: kTitleTertiary
                  text: 'Plays in Library'
                }
              }
            }

            Column {
              spacing: 5

              width: parent.width
              
              // TODO: Move styles for selectable text to component
              TextEdit {
                id: textEdit

                color: '#FFF'
                readOnly: true
                renderType: Text.NativeRendering
                selectByMouse: true
                selectionColor: Qt.rgba(255, 255, 255, 0.15)
                text: canDisplayEntireScrobble ? viewModel.scrobbleData.artist.bio : ''
                wrapMode: Text.Wrap

                font {
                  letterSpacing: 0.25
                  weight: Font.Medium
                }

                width: parent.width

                TextContextMenu {
                  text: textEdit

                  anchors.fill: parent
                }
              }

              Link {
                text: 'Read more on Last.fm'
                address: canDisplayEntireScrobble && viewModel.scrobbleData.artist.lastfm_url
                visible: canDisplayEntireScrobble && viewModel.scrobbleData.artist.bio
              }
            }
          }
        }
      }
    }

    WheelScrollArea {
      flickable: scrollArea

      anchors.fill: scrollArea
    }
  }
}
