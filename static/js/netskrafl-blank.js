// Handles logic related to handling blank tiles, i.e. if tiles are dropped
// that are blank, a blank tile dialog shows

function blankFlasher() {
   // Flash a frame around the target square for a blank tile
   var target = $("#blank-dialog").data("param").target;
   if (target !== undefined)
      $(target).toggleClass("over");
}

function keyBlankDialog(ev, combo) {
   /* Handle a key press from Mousetrap: close the blank dialog with the indicated letter chosen */
   var letter = combo;
   if (letter == "esc")
      letter = "";
   else
   if (letter.indexOf("shift+") === 0)
      letter = letter.charAt(6);
   closeBlankDialog({ data: letter });
}

function openBlankDialog(elDragged, target) {
   /* Show the modal dialog to prompt for the meaning of a blank tile */
   // Hide the blank in its original position
   $(elDragged).css("visibility", "hidden");
   // Flash a frame around the target square
   var iv = window.setInterval(blankFlasher, 500);
   // Show the dialog
   $("#blank-dialog")
      .data("param", { eld: elDragged, target: target, ival: iv })
      .css("visibility", "visible");
   // Reset the esc key to make it close the dialog
   Mousetrap.bind('esc', keyBlankDialog);
   // Bind all normal keys to make them select a letter and close the dialog
   for (var i = 0; i < LEGAL_LETTERS.length; i++) {
      Mousetrap.bind(LEGAL_LETTERS[i], keyBlankDialog);
      Mousetrap.bind("shift+" + LEGAL_LETTERS[i], keyBlankDialog);
   }
}

function closeBlankDialog(ev) {
   /* The blank tile dialog is being closed: place the tile as instructed */
   // ev.data contains the tile selected, or "" if none
   var letter = (!ev) ? "" : ev.data;
   var param = $("#blank-dialog").data("param");
   // The DIV for the blank tile being dragged
   var eld = param.eld;
   // The target TD for the tile
   var target = param.target;
   // Stop flashing
   window.clearInterval(param.ival);
   // Remove the highlight of the target square, if any
   $(target).removeClass("over");
   $(eld).css("visibility", "visible");
   if (letter !== "") {
      // Place the blank tile with the indicated meaning on the board
      $(eld).data("letter", letter);
      $(eld).addClass("blanktile");
      eld.childNodes[0].nodeValue = letter;
      eld.parentNode.removeChild(eld);
      target.appendChild(eld);
   }
   // Hide the dialog
   $("#blank-dialog")
      .data("param", null)
      .css("visibility", "hidden");
   // Make sure that all yellow frames are removed
   $("#blank-meaning").find("td").removeClass("over");
   // Rebind the Esc key to the resetRack() function
   Mousetrap.bind('esc', resetRack);
   // Unbind the alphabetic letters
   for (var i = 0; i < LEGAL_LETTERS.length; i++) {
      Mousetrap.unbind(LEGAL_LETTERS[i]);
      Mousetrap.unbind("shift+" + LEGAL_LETTERS[i]);
   }
   saveTiles();
   updateButtonState();
}

function prepareBlankDialog() {
   /* Construct the blank tile dialog DOM to make it ready for display */
   var bt = $("#blank-meaning");
   bt.html("");
   // Create tile TDs and DIVs for all legal letters
   var len = LEGAL_LETTERS.length;
   var ix = 0;
   while (len > 0) {
      /* Rows */
      var str = "<tr>";
      /* Columns: max BLANK_TILES_PER_LINE tiles per row */
      for (var i = 0; i < BLANK_TILES_PER_LINE && len > 0; i++) {
         var tile = LEGAL_LETTERS[ix++];
         str += "<td><div class='blank-choice'>" + tile + "</div></td>";
         len--;
      }
      str += "</tr>";
      bt.append(str);
   }
   /* Add a click handler to each tile, calling closeBlankDialog with the
      associated letter as an event parameter */
   $("div.blank-choice").addClass("tile").addClass("racktile").each(function() {
      $(this).click($(this).text(), closeBlankDialog);
   });
   // Show a yellow frame around the letter under the mouse pointer
   bt.find("td").hover(
      function() { $(this).addClass("over"); },
      function() { $(this).removeClass("over"); }
   );
   // Make the close button close the dialog
   $("#blank-close").click("", closeBlankDialog);
}

