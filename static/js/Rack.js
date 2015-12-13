///// RACK ///////////////
var Rack = function() {
}

Rack.prototype.rescramble = function(ev) {
   /* Reorder the rack randomly. Bound to the Backspace key. */
   if (showingDialog)
      return false;
   resetRack(ev);
   var array = [];
   var i, rackTileId;
   for (i = 1; i <= RACK_SIZE; i++) {
      rackTileId = "R" + i.toString();
      array.push(document.getElementById(rackTileId).firstChild);
   }
   var currentIndex = array.length, temporaryValue, randomIndex;
   // Fisher-Yates (Knuth) shuffle algorithm
   while (0 !== currentIndex) {
      randomIndex = Math.floor(Math.random() * currentIndex);
      currentIndex -= 1;
      temporaryValue = array[currentIndex];
      array[currentIndex] = array[randomIndex];
      array[randomIndex] = temporaryValue;
   }
   for (i = 1; i <= RACK_SIZE; i++) {
      rackTileId = "R" + i.toString();
      var elem = document.getElementById(rackTileId);
      if (elem.firstChild !== null)
         elem.removeChild(elem.firstChild);
      if (array[i-1] !== null)
         elem.appendChild(array[i-1]);
   }
   saveTiles();
   return false; // Stop default behavior
};

