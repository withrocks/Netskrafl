var INPUT_STATE_NONE = 0;
var INPUT_STATE_DRAGGING = 1;
var INPUT_STATE_SINGLE_CLICKING = 2;
var INPUT_STATE_TYPING_H = 3;
var INPUT_STATE_TYPING_V = 4;
var HORIZONTAL = 1;
var VERTICAL = 2;

var typingLine = null; /* An array of elements being typed in, such as ['A1',..., 'A7'] */
var typingLineIndex = -1; /* An index to the current element being typed in the typingLine */
var inputState = INPUT_STATE_NONE;
var typingStartedAt = null;

function typingMoveUp() {
    // Move the current item from the rack and up:
    var coord = "#R" + typingRackIndex;
    //var vector = toVector(coord);
    // TODO: Assuming it's not empty, check firstChild null for that
    // (and then we need to encapsulate this better)

    var elem = $(coord).get(0);

    if (elem.firstChild) {
        var tile = elem.firstChild;
        console.log("Moving", coord, tile);
        moveToTypingLine(tile);
    }

    // Advance the "pointer"
    setTypingRackIndex(typingRackIndex + 1);
}

function typingMoveDown() {
    setTypingRackIndex(typingRackIndex - 1);

    var target = $("#R" + typingRackIndex).get(0);
    var sourceId = typingLine[typingLineIndex];
    var source = $("#" + sourceId).get(0).firstChild;

    console.log(target, source);
    moveTile(source, target);
    typingLineIndex -= 1;
}

function handleTypingKeypress(ev, combo) {
    // If in 'typing' mode, the user can directly type
    // letters from the rack
    console.log(ev, combo);
    ev.preventDefault();

    if (combo == "esc") {
        // Exit typing mode
    }
    else if (combo == "up") {
        // Move the currently selected element from the rack to the line
        typingMoveUp();
    }
    else if (combo == "down") {
        typingMoveDown();
    }
    else if (combo == "right") {
        setTypingRackIndex(typingRackIndex + 1);
    }
    else if (combo == "left") {
        setTypingRackIndex(typingRackIndex - 1);
    }
}

function unbindRackIdentifiers() {
   for (var i = 1; i <= 7; i++) {
      Mousetrap.unbind("" + i);
   }
}

function bindRackIdentifiers(callback) {
   // NOTE: The idea was originally to bind to the actual
   // characters, but it seems that browsers don't support
   // letters that need two keystrokes (e.g. é).
   // So instead, the arrow keys are bound
   /*for (var i = 1; i <= 7; i++) {
      Mousetrap.bind(i + "", callback);
   }*/
   Mousetrap.bind("up", callback);
   Mousetrap.bind("down", callback);
   Mousetrap.bind("left", callback);
   Mousetrap.bind("right", callback);
}

function setInputState(state) {
    var lastState = inputState;
    inputState = state;

    // Always reset the input state via this method only
    console.log("Setting input state: " + lastState + "=>" + state);

    if (lastState == INPUT_STATE_TYPING_H ||
        lastState == INPUT_STATE_TYPING_V) {
        clearTyping();
    }

    if (inputState == INPUT_STATE_NONE) {
        // Reset every state variable, no matter if it was set or not:
        selectTile(null);
        elementDragged = null;
        tileSelected = null;
        clearTyping();
    }
    else if (inputState == INPUT_STATE_DRAGGING) {
        // Remove selection, if any
        selectTile(null);
    }
    else if (inputState == INPUT_STATE_TYPING_H ||
             inputState == INPUT_STATE_TYPING_V) {
        bindRackIdentifiers(handleTypingKeypress);
    }
}

/*
Supports enumerating over a certain number of squares,
with the possibility of jumping if occupied

  start: start from this square (e.g. A1)
  max: Enumerate at most these items
  direction: HORIZONTAL or VERTICAL
  jumpIfOccupied: Ignore occupied squares
  callback: Callback for yielding
*/
function enumerateSquares(start, max, direction, jumpIfOccupied, callback) {
    var enumerateCount = 0;
    var vector = toVector(start);
    var row = vector.row;
    var col = vector.col;

    var moveVector;
    if (direction == HORIZONTAL)
        moveVector = {row: 0, col: 1};
    else
        moveVector = {row: 1, col: 0};

    // While loop since the conditions will become a bit more complex with jumps
    while (true) {
        if (enumerateCount == max) {
            console.log("Enumerated the requested number of items") ;
            break;
        }
        else if (col > BOARD_SIZE || row > BOARD_SIZE) {
            console.log("Off the board, exiting");
            break;
        }

        var currentId = coord(row, col);
        var tile = tileAt(row, col);

        // Move (doing it here to ensure a break out of the while loop)
        row += moveVector.row;
        col += moveVector.col;

        if (jumpIfOccupied) {
            var current = $("#" + currentId);

            if (tile !== null) {
                console.log("Jumping...");
                continue;
            }
        }

        // Yield the current:
        callback(currentId);
        enumerateCount++;
    }
}

// Returns an array with squares that can be filled with tiles
function validInputLine(start, direction) {
    var ret = [];
    enumerateSquares(start, 7, direction, true, function(id) {
        ret.push(id);
    });
    return ret;
}

function clearTyping() {
   $(".typing").removeClass("typing")
        .removeClass("typing-vertical")
        .removeClass("typing-horizontal")
        .removeClass("typing-start")
        .removeClass("typing-end");
   $(".typing-next").removeClass("typing-next");
}

// Moves the element from the rack tile to the "typingLine"
// and advances the typing line pointer
function moveToTypingLine(rackTile) {
    typingLineIndex += 1; // Always initialized to -1
    var targetId = typingLine[typingLineIndex];
    var target = $("#" + targetId).get(0);
    moveTile(rackTile, target);
}

function setTypingRackIndex(index) {
   // NOTE: I want the 8, since it provides the expected UX (for now)
   if (index < 1 || index > 8) return;

   $(".typing-next").removeClass("typing-next");
   typingRackIndex = index;
   $("#R" + typingRackIndex).addClass("typing-next");
}

function selectTypingLine(startSquare, order) {
    // Set the line being typed:
   typingLine = validInputLine(startSquare, order);
   typingLineIndex = -1;
   typingStartedAt = startSquare;

   // Furthermore, indicate that the first (TODO: non-empty) item
   // in the rack will go up if "up" is pressed
   setTypingRackIndex(1);

   // Visual indication:
   var length = typingLine.length;
   for (var index in typingLine) {
      var id = typingLine[index];
      var detailClass = order == HORIZONTAL ? "typing-horizontal" :
        "typing-vertical";

      var item = $("#" + id);
      item.addClass("typing").addClass(detailClass);
      if (index === 0)
        item.addClass("typing-start");
      else if (index == length - 1)
        item.addClass("typing-end");
   }
}

// TODO: Fix indent!
// TODO: Move to separate class and encapsulate in a prototype
function onBoardSquareClicked() {
    // TODO: Only go to vertical from horizontal on the same square

    // Start 'typing' mode if clicking anywhere on the board
    if (inputState == INPUT_STATE_NONE) {
       setInputState(INPUT_STATE_TYPING_H);
       clearTyping();
       selectTypingLine(this.id, HORIZONTAL);
    }
    else if (inputState == INPUT_STATE_TYPING_H) {
       setInputState(INPUT_STATE_TYPING_V);
       clearTyping();
       selectTypingLine(this.id, VERTICAL);
    }
    else if (inputState == INPUT_STATE_TYPING_V) {
       setInputState(INPUT_STATE_NONE);
       console.log("Clearing typing state");
    }
    else if (inputState == INPUT_STATE_SINGLE_CLICKING) {
        // TODO: Not able to single click to rack, was that introduced now?
       moveSelectedTile(this);
    }
}
