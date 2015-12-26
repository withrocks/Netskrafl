// Logic that has to do with movement of tiles
// to/from the rack to the board
// All global variables in this file are "private" to the file,
// that is by convention not used in another file.
// Same goes for functions, except these:
//   initDraggable
//   initDropTargets
//   initRackDraggable

var elementDragged = null; /* The element being dragged with the mouse */
var tileSelected = null; /* The selected (single-clicked) tile */

function moveSelectedTile(sq) {
   // Move the tileSelected to the target square
   if (sq.firstChild === null) {
      moveTile(tileSelected, sq);
      selectTile(null);
   }
}

function selOver(sq) {
   if (sq.firstChild === null)
      // Legitimate drop target
      $(sq).addClass("sel");
}

function selOut(sq) {
   $(sq).removeClass("sel");
}

function selectTile(elem) {
   if (elem === tileSelected) {
      if (elem === null)
         // Nothing was selected - nothing to do
         return;
      // Re-clicking on an already selected tile:
      // remove the selection
      $(elem).removeClass("sel");
      tileSelected = null;
   }
   else {
      // Changing the selection
      if (tileSelected !== null)
         $(tileSelected).removeClass("sel");
      tileSelected = elem;
      if (tileSelected !== null)
         $(tileSelected).addClass("sel");
   }
   if (tileSelected !== null) {
      // We have a selected tile: show a red square around
      // drop targets for it
      $("table.board td.ui-droppable").hover(
         function() { selOver(this); },
         function() { selOut(this); }
      ).click(
         function() { moveSelectedTile(this); }
      );
   }
   else {
      // No selected tile: no hover
      $("table.board td.ui-droppable").off("mouseenter mouseleave click").removeClass("sel");
   }
}

function handleDragstart(e, ui) {
   // Remove selection, if any
   selectTile(null);
   // Remove the blinking sel class from the drag clone, if there
   $("div.ui-draggable-dragging").removeClass("sel");
   // The dragstart target is the DIV inside a TD
   elementDragged = e.target;
   // The original tile, still shown while dragging
   elementDragged.style.opacity = "0.5";
}

function handleDragend(e, ui) {
   if (elementDragged !== null)
      elementDragged.style.opacity = null; // "1.0";
   elementDragged = null;
}

function handleDropover(e, ui) {
   if (e.target.id.charAt(0) == 'R' || e.target.firstChild === null)
     /* Rack square or empty square: can drop. Add yellow outline highlight to square */
     this.classList.add("over");
}

function handleDropleave(e, ui) {
   /* Can drop here: remove outline highlight from square */
   this.classList.remove("over");
}

function initDraggable(elem) {
   /* The DIVs inside the board TDs are draggable */
   $(elem).draggable(
      {
         opacity : 0.9,
         helper : "clone",
         cursor : "pointer",
         zIndex : 100,
         start : handleDragstart,
         stop : handleDragend
      }
   );
   $(elem).click(function(ev) { selectTile(this); ev.stopPropagation(); });
}

function removeDraggable(elem) {
   /* The DIVs inside the board TDs are draggable */
   $(elem).draggable("destroy");
   if (elem === tileSelected)
      selectTile(null);
   $(elem).off("click");
}

function initRackDraggable(state) {
   /* Make the seven tiles in the rack draggable or not, depending on
      the state parameter */
   $("div.racktile").each(function() {
      if (!$(this).hasClass("ui-draggable-dragging")) {
         var sq = $(this).parent().attr("id");
         var rackTile = document.getElementById(sq);
         if (rackTile && rackTile.firstChild)
            /* There is a tile in this rack slot */
            if (state)
               initDraggable(rackTile.firstChild);
            else
               removeDraggable(rackTile.firstChild);
      }
   });
}

function initDropTarget(elem) {
   /* Prepare a board square or a rack slot to accept drops */
   if (elem !== null)
      elem.droppable(
         {
            drop : handleDrop,
            over : handleDropover,
            out : handleDropleave
         }
      );
}

function initDropTargets() {
   /* All board squares are drop targets */
   var x, y, sq;
   for (x = 0; x < BOARD_SIZE; x++)
      for (y = 0; y < BOARD_SIZE; y++) {
         sq = $("#" + coord(y, x));
         initDropTarget(sq);
      }
   /* Make the rack a drop target as well */
   for (x = 1; x <= RACK_SIZE; x++) {
      sq = $("#R" + x.toString());
      initDropTarget(sq);
   }
   /* Make the background a drop target */
   initDropTarget($("#container"));
}

function moveTile(src, target) {
   // src is a DIV; target is a TD
   var ok = true;
   var parentid = src.parentNode.id;
   if (parentid.charAt(0) == 'R') {
      /* Dropping from the rack */
      var t = $(src).data("tile");
      var dropToRack = (target.id.charAt(0) == 'R');
      if (!dropToRack && t == '?') {
         /* Dropping a blank tile on to the board: we need to ask for its meaning */
         openBlankDialog(src, target);
         ok = false; // The drop will be completed later, when the blank dialog is closed
      }
   }
   if (ok) {
      /* Complete the drop */
      src.parentNode.removeChild(src);
      target.appendChild(src);
      if (target.id.charAt(0) == 'R') {
         /* Dropping into the rack */
         if ($(src).data("tile") == '?') {
            /* Dropping a blank tile: erase its letter value, if any */
            $(src).data("letter", ' ');
            src.childNodes[0].nodeValue = "\xa0"; // Non-breaking space, i.e. &nbsp;
         }
      }
      // Save this state in local storage,
      // to be restored when coming back to this game
      saveTiles();
   }
   updateButtonState();
}

function handleDrop(e, ui) {
   /* A tile is being dropped on a square on the board or into the rack */
   e.target.classList.remove("over");
   /* Save the elementDragged value as it will be set to null in handleDragend() */
   var eld = elementDragged;
   if (eld === null)
      return;
   var i, rslot;
   eld.style.opacity = null; // "1.0";
   if (e.target.id == "container") {
      // Dropping to the background container:
      // shuffle things around so it looks like we are dropping to the first empty rack slot
      rslot = null;
      for (i = 1; i <= RACK_SIZE; i++) {
         rslot = document.getElementById("R" + i.toString());
         if (!rslot.firstChild)
            /* Empty slot in the rack */
            break;
         rslot = null;
      }
      if (!rslot)
         return; // Shouldn't really happen
      e.target = rslot;
   }
   var dropToRack = (e.target.id.charAt(0) == 'R');
   if (dropToRack && e.target.firstChild !== null) {
      /* Dropping into an already occupied rack slot: shuffle the rack tiles to make room */
      var ix = parseInt(e.target.id.slice(1));
      rslot = null;
      i = 0;
      /* Try to find an empty slot to the right */
      for (i = ix + 1; i <= RACK_SIZE; i++) {
         rslot = document.getElementById("R" + i.toString());
         if (!rslot.firstChild)
            /* Empty slot in the rack */
            break;
         rslot = null;
      }
      if (rslot === null) {
         /* Not found: Try an empty slot to the left */
         for (i = ix - 1; i >= 1; i--) {
            rslot = document.getElementById("R" + i.toString());
            if (!rslot.firstChild)
               /* Empty slot in the rack */
               break;
            rslot = null;
         }
      }
      if (rslot === null) {
         /* No empty slot: must be internal shuffle in the rack */
         rslot = eld.parentNode;
         i = parseInt(rslot.id.slice(1));
      }
      if (rslot !== null) {
         var j, src, tile;
         if (i > ix)
            /* Found empty slot: shift rack tiles to the right to make room */
            for (j = i; j > ix; j--) {
               src = document.getElementById("R" + (j - 1).toString());
               tile = src.firstChild;
               src.removeChild(tile);
               rslot.appendChild(tile);
               rslot = src;
            }
         else
         if (i < ix)
            /* Found empty slot: shift rack tiles to the left to make room */
            for (j = i; j < ix; j++) {
               src = document.getElementById("R" + (j + 1).toString());
               tile = src.firstChild;
               src.removeChild(tile);
               rslot.appendChild(tile);
               rslot = src;
            }
      }
   }
   if (e.target.firstChild === null) {
      /* Looks like a legitimate drop */
      moveTile(eld, e.target);
   }
   elementDragged = null;
}

