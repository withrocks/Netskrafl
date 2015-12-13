/* Handles the different ways of getting tiles on the board
   by the user and the state of these

   User can:
     1. drag/drop tiles
     2. press a tile in the rack and drop it without having to drag
     3. (experimental) select an area to fill in either V or H direction
        and write the word or select tiles from the rack
   */
var MoveMechanics = function() {
    this.elementDragged = null; /* The element being dragged with the mouse */
    this.tileSelected = null; /* The selected (single-clicked) tile */
}

MoveMechanics.prototype.moveTile = function(src, target) {
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
};

MoveMechanics.prototype.moveSelectedTile = function(sq) {
   // Move the tileSelected to the target square
   if (sq.firstChild === null) {
      this.moveTile(this.tileSelected, sq);
      this.selectTile(null);
   }
}

MoveMechanics.prototype.selectTile = function(elem) {
   if (elem === this.tileSelected) {
      if (elem === null)
         // Nothing was selected - nothing to do
         return;
      // Re-clicking on an already selected tile:
      // remove the selection
      $(elem).removeClass("sel");
      this.tileSelected = null;
   }
   else {
      // Changing the selection
      if (this.tileSelected !== null)
         $(this.tileSelected).removeClass("sel");
      this.tileSelected = elem;
      if (this.tileSelected !== null)
         $(this.tileSelected).addClass("sel");
   }
   if (this.tileSelected !== null) {
      // We have a selected tile: show a red square around
      // drop targets for it
      $("table.board td.ui-droppable").hover(
         function() { selOver(this); },
         function() { selOut(this); }
      ).click(
         function() { skrafl.moveMechanics.moveSelectedTile(this); }
      );
   }
   else {
      // No selected tile: no hover
      $("table.board td.ui-droppable").off("mouseenter mouseleave click").removeClass("sel");
   }
}

MoveMechanics.prototype.handleDragstart = function(e, ui) {
   // NOTE: `this` will NOT apply to the moveMechanics object, as this will
   // be applied to a tile being dragged
   // Remove selection, if any
   skrafl.moveMechanics.selectTile(null); // NOTE: Can't reference this as it will be applied to a tile
   // Remove the blinking sel class from the drag clone, if there
   $("div.ui-draggable-dragging").removeClass("sel");
   // The dragstart target is the DIV inside a TD
   skrafl.moveMechanics.elementDragged = e.target;
   // The original tile, still shown while dragging
   skrafl.moveMechanics.elementDragged.style.opacity = "0.5";
}

MoveMechanics.prototype.initDraggable = function(elem) {
   skrafl.log("initDraggable");
   /* The DIVs inside the board TDs are draggable */
   $(elem).draggable(
      {
         opacity : 0.9,
         helper : "clone",
         cursor : "pointer",
         zIndex : 100,
         start : skrafl.moveMechanics.handleDragstart,
         stop : handleDragend
      }
   );
   $(elem).click(function(ev) { skrafl.moveMechanics.selectTile(this); ev.stopPropagation(); });
}

MoveMechanics.prototype.removeDraggable = function(elem) {
   skrafl.log("removeDraggable");
   /* The DIVs inside the board TDs are draggable */
   $(elem).draggable("destroy");
   if (elem === tileSelected)
      this.selectTile(null);

   console.log("Removing click event");
   $(elem).off("click");  // TODO: removes other click events
}

MoveMechanics.prototype.initRackDraggable = function(state) {
    skrafl.log("initRackDraggable");
   /* Make the seven tiles in the rack draggable or not, depending on
      the state parameter */
   $("div.racktile").each(function() {
      if (!$(this).hasClass("ui-draggable-dragging")) {
         var sq = $(this).parent().attr("id");
         var rackTile = document.getElementById(sq);
         if (rackTile && rackTile.firstChild)
            /* There is a tile in this rack slot */
            console.log(this);
            if (state)
               skrafl.moveMechanics.initDraggable(rackTile.firstChild);
            else
               skrafl.moveMechanics.removeDraggable(rackTile.firstChild);
      }
   });
}

MoveMechanics.prototype.handleDrop = function(e, ui) {
    skrafl.log("handleDrop");
   /* A tile is being dropped on a square on the board or into the rack */
   e.target.classList.remove("over");
   /* Save the elementDragged value as it will be set to null in handleDragend() */
   var eld = skrafl.moveMechanics.elementDragged;
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
      skrafl.moveMechanics.moveTile(eld, e.target);
   }
   skrafl.moveMechanics.elementDragged = null;
}

// Methods that will be applied to each tile when applicable
// TODO: add to the class to get the "namespace" of MoveMechanics
// but make a note of that the this pointer will not be that instance
function handleDragend(e, ui) {
   if (skrafl.moveMechanics.elementDragged !== null)
      skrafl.moveMechanics.elementDragged.style.opacity = null; // "1.0";
   skrafl.moveMechanics.elementDragged = null;
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

