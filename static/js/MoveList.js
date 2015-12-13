// The move list shows the history of moves
var MoveList = function() {
};

MoveList.prototype.highlightMove = function(ev) {
   /* Highlight a move's tiles when hovering over it in the move list */
   var co = ev.data.coord;
   var tiles = ev.data.tiles;
   var playerColor = ev.data.player;
   var vec = toVector(co);
   var col = vec.col;
   var row = vec.row;
   for (var i = 0; i < tiles.length; i++) {
      var tile = tiles.charAt(i);
      if (tile == '?')
         continue;
      var sq = coord(row, col);
      var tileDiv = $("#"+sq).children().eq(0);
      if (ev.data.show)
         tileDiv.addClass("highlight" + playerColor);
      else
         tileDiv.removeClass("highlight" + playerColor);
      col += vec.dx;
      row += vec.dy;
   }
   if (ev.data.show)
      /* Add a highlight to the score */
      $(this).find("span.score").addClass("highlight");
   else
      /* Remove highlight from score */
      $(this).find("span.score").removeClass("highlight");
};

MoveList.prototype.appendMove = function(player, co, tiles, score) {
   /* Add a move to the move history list */
   var wrdclass = "wordmove";
   var rawCoord = co;
   var tileMove = false;
   if (co === "") {
      /* Not a regular tile move */
      wrdclass = "othermove";
      if (tiles == "PASS")
         /* Pass move */
         tiles = "Pass";
      else
      if (tiles.indexOf("EXCH") === 0) {
         /* Exchange move - we don't show the actual tiles exchanged, only their count */
         var numtiles = tiles.slice(5).length;
         tiles = "Skipti um " + numtiles.toString() + (numtiles == 1 ? " staf" : " stafi");
      }
      else
      if (tiles == "RSGN")
         /* Resigned from game */
         tiles = " Gaf viðureign"; // Extra space intentional
      else
      if (tiles == "TIME") {
         /* Overtime adjustment */
         tiles = " Umframtími "; // Extra spaces intentional
      }
      else
      if (tiles == "OVER") {
         /* Game over */
         tiles = "Viðureign lokið";
         wrdclass = "gameover";
         gameOver = true;
      }
      else {
         /* The rack leave at the end of the game (which is always in lowercase
            and thus cannot be confused with the above abbreviations) */
         wrdclass = "wordmove";
      }
   }
   else {
      co = "(" + co + ")";
      // Note: String.replace() will not work here since there may be two question marks in the string
      tiles = tiles.split("?").join(""); /* !!! TODO: Display wildcard characters differently? */
      tileMove = true;
   }
   /* Update the scores */
   if (player === 0)
      leftTotal = Math.max(leftTotal + score, 0);
   else
      rightTotal = Math.max(rightTotal + score, 0);
   var str;
   var title = tileMove ? 'title="Smelltu til að fletta upp" ' : "";
   if (wrdclass == "gameover") {
      str = '<div class="move gameover"><span class="gameovermsg">' + tiles + '</span>' +
         '<span class="statsbutton" onclick="navToReview()">Skoða yfirlit</span></div>';
      // Show a congratulatory message if the local player is the winner
      var winner = -2; // -1 is reserved
      if (leftTotal > rightTotal)
         winner = 0;
      else
      if (leftTotal < rightTotal)
         winner = 1;
      if (localPlayer() == winner) {
         $("#congrats").css("visibility", "visible");
         if (!initializing || gameIsZombie()) {
            // The local player is winning in real time or opening the
            // game for the first time after winning it in absentia:
            // Play fanfare sound if audio enabled
            var youWin = document.getElementById("you-win");
            if (youWin)
               youWin.play();
         }
      }
      // Show the Facebook share button if the game is over
      $("div.fb-share").css("visibility", "visible");
      // Clear local storage, if any
      clearTiles();
   }
   else
   if (player === 0) {
      /* Left side player */
      str = '<div ' + title + 'class="move leftmove">' +
         '<span class="total">' + leftTotal + '</span>' +
         '<span class="score">' + score + '</span>' +
         '<span class="' + wrdclass + '"><i>' + tiles + '</i> ' +
         co + '</span>' +
         '</div>';
   }
   else {
      /* Right side player */
      str = '<div ' + title + 'class="move rightmove">' +
         '<span class="' + wrdclass + '">' + co +
         ' <i>' + tiles + '</i></span>' +
         '<span class="score">' + score + '</span>' +
         '<span class="total">' + rightTotal + '</span>' +
         '</div>';
   }
   var movelist = $("div.movelist");
   movelist.append(str);
   if (wrdclass != "gameover") {
      var m = movelist.children().last();
      var playerColor = "0";
      var lcp = localPlayer();
      if (player === lcp || (lcp == -1 && player === 0))
         m.addClass("humangrad" + (player === 0 ? "_left" : "_right")); /* Local player */
      else {
         m.addClass("autoplayergrad" + (player === 0 ? "_left" : "_right")); /* Remote player */
         playerColor = "1";
      }
      if (tileMove) {
         /* Register a hover event handler to highlight this move */
         m.on("mouseover",
            { coord: rawCoord, tiles: tiles, score: score, player: playerColor, show: true },
            this.highlightMove
         );
         m.on("mouseout",
            { coord: rawCoord, tiles: tiles, score: score, player: playerColor, show: false },
            this.highlightMove
         );
         // Clicking on a word in the word list looks up the word on the official word list website
         m.on("click",
            { tiles: tiles },
            lookupWord
         );
      }
   }
   /* Manage the scrolling of the move list */
   var lastchild = $("div.movelist .move").last();
   var firstchild = $("div.movelist .move").first();
   var topoffset = lastchild.position().top -
      firstchild.position().top +
      lastchild.outerHeight();
   var height = movelist.height();
   if (topoffset >= height)
      movelist.scrollTop(topoffset - height);
   /* Count the moves */
   numMoves += 1;
   if (tileMove)
      numTileMoves += 1;
}


