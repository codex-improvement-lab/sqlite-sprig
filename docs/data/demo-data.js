window.SPRIG_DEMO = {
  "authoredExample": true,
  "source": {
    "spaces": [
      {
        "id": 1,
        "name": "Studio"
      },
      {
        "id": 2,
        "name": "Archive"
      }
    ],
    "boards": [
      {
        "id": 10,
        "space_id": 1,
        "name": "Build"
      },
      {
        "id": 20,
        "space_id": 2,
        "name": "Archive"
      }
    ],
    "users": [
      {
        "id": 1,
        "space_id": 1,
        "name": "Mara"
      },
      {
        "id": 2,
        "space_id": 1,
        "name": "Jules"
      },
      {
        "id": 3,
        "space_id": 1,
        "name": "Ivo"
      },
      {
        "id": 4,
        "space_id": 2,
        "name": "Sol"
      }
    ],
    "cards": [
      {
        "id": 101,
        "board_id": 10,
        "creator_id": 3,
        "title": "Search filters",
        "status": "open",
        "comment_count": 2
      },
      {
        "id": 102,
        "board_id": 20,
        "creator_id": 4,
        "title": "Earlier release",
        "status": "open",
        "comment_count": 2
      },
      {
        "id": 103,
        "board_id": 10,
        "creator_id": 1,
        "title": "Checkout review",
        "status": "open",
        "comment_count": 2
      }
    ],
    "comments": [
      {
        "id": 201,
        "card_id": 101,
        "author_id": 3,
        "body": "Check empty results"
      },
      {
        "id": 202,
        "card_id": 102,
        "author_id": 4,
        "body": "First review"
      },
      {
        "id": 203,
        "card_id": 103,
        "author_id": 1,
        "body": "Check tab order"
      },
      {
        "id": 204,
        "card_id": 103,
        "author_id": 2,
        "body": "Confirm mobile layout"
      },
      {
        "id": 205,
        "card_id": 101,
        "author_id": 2,
        "body": "Shared reviewer"
      },
      {
        "id": 206,
        "card_id": 102,
        "author_id": 4,
        "body": "Release note"
      }
    ],
    "card_labels": [
      {
        "card_id": 101,
        "label_id": 100
      },
      {
        "card_id": 102,
        "label_id": 102
      },
      {
        "card_id": 103,
        "label_id": 100
      },
      {
        "card_id": 103,
        "label_id": 101
      }
    ],
    "labels": [
      {
        "id": 100,
        "space_id": 1,
        "name": "bug"
      },
      {
        "id": 101,
        "space_id": 1,
        "name": "ui"
      },
      {
        "id": 102,
        "space_id": 2,
        "name": "archive"
      }
    ]
  },
  "sourceRows": 24,
  "cases": {
    "103": {
      "totalRows": 11,
      "rows": {
        "spaces": [
          {
            "id": 1,
            "name": "Studio"
          }
        ],
        "boards": [
          {
            "id": 10,
            "space_id": 1,
            "name": "Build"
          }
        ],
        "users": [
          {
            "id": 1,
            "space_id": 1,
            "name": "Mara"
          },
          {
            "id": 2,
            "space_id": 1,
            "name": "Jules"
          }
        ],
        "cards": [
          {
            "id": 103,
            "board_id": 10,
            "creator_id": 1,
            "title": "Checkout review",
            "status": "open",
            "comment_count": 2
          }
        ],
        "comments": [
          {
            "id": 203,
            "card_id": 103,
            "author_id": 1,
            "body": "Check tab order"
          },
          {
            "id": 204,
            "card_id": 103,
            "author_id": 2,
            "body": "Confirm mobile layout"
          }
        ],
        "card_labels": [
          {
            "card_id": 103,
            "label_id": 100
          },
          {
            "card_id": 103,
            "label_id": 101
          }
        ],
        "labels": [
          {
            "id": 100,
            "space_id": 1,
            "name": "bug"
          },
          {
            "id": 101,
            "space_id": 1,
            "name": "ui"
          }
        ]
      },
      "filename": "card-103.sqlite3",
      "sha256": "a5d037db8788a2989e2c4428603e86061494e6776c7eab40e88906c55a82fbc4"
    },
    "101": {
      "totalRows": 9,
      "rows": {
        "spaces": [
          {
            "id": 1,
            "name": "Studio"
          }
        ],
        "boards": [
          {
            "id": 10,
            "space_id": 1,
            "name": "Build"
          }
        ],
        "users": [
          {
            "id": 2,
            "space_id": 1,
            "name": "Jules"
          },
          {
            "id": 3,
            "space_id": 1,
            "name": "Ivo"
          }
        ],
        "cards": [
          {
            "id": 101,
            "board_id": 10,
            "creator_id": 3,
            "title": "Search filters",
            "status": "open",
            "comment_count": 2
          }
        ],
        "comments": [
          {
            "id": 201,
            "card_id": 101,
            "author_id": 3,
            "body": "Check empty results"
          },
          {
            "id": 205,
            "card_id": 101,
            "author_id": 2,
            "body": "Shared reviewer"
          }
        ],
        "card_labels": [
          {
            "card_id": 101,
            "label_id": 100
          }
        ],
        "labels": [
          {
            "id": 100,
            "space_id": 1,
            "name": "bug"
          }
        ]
      },
      "filename": "card-101.sqlite3",
      "sha256": "003c6cbddf8edfaa1a9673af1312dac8203956fc8b3c234c0891ba1c19b4fb4b"
    },
    "102": {
      "totalRows": 8,
      "rows": {
        "spaces": [
          {
            "id": 2,
            "name": "Archive"
          }
        ],
        "boards": [
          {
            "id": 20,
            "space_id": 2,
            "name": "Archive"
          }
        ],
        "users": [
          {
            "id": 4,
            "space_id": 2,
            "name": "Sol"
          }
        ],
        "cards": [
          {
            "id": 102,
            "board_id": 20,
            "creator_id": 4,
            "title": "Earlier release",
            "status": "open",
            "comment_count": 2
          }
        ],
        "comments": [
          {
            "id": 202,
            "card_id": 102,
            "author_id": 4,
            "body": "First review"
          },
          {
            "id": 206,
            "card_id": 102,
            "author_id": 4,
            "body": "Release note"
          }
        ],
        "card_labels": [
          {
            "card_id": 102,
            "label_id": 102
          }
        ],
        "labels": [
          {
            "id": 102,
            "space_id": 2,
            "name": "archive"
          }
        ]
      },
      "filename": "card-102.sqlite3",
      "sha256": "9308c79deec2eb80afcad06dea9ef8ed443c46c69582eea9829971a167ee14bf"
    }
  },
  "sourceSha256": "8b225feb2aacfdd67165ea575d49873ebdd0b757e86d364407518dca4101a279",
  "sourceFilename": "board.sqlite3"
};
