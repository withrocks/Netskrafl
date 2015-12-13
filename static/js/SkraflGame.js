//// SKRAFL GAME MANAGEMENT OBJECT ///
// This is the main "app" class, initializes all other objects
var SkraflGame = function(debug) {
    console.log("Initialize skrafl...");
    this.clockLeft = new Clock("clockleft", 0);
    this.clockRight = new Clock("clockright", 1);
    this.rack = new Rack();
    this.scoreLeft = new ScoreBoard('scoreleft');
    this.scoreRight = new ScoreBoard('scoreright');
    this.moveList = new MoveList();
    this.moveMechanics = new MoveMechanics();

    if (debug) {
        // TODO: Parameter?
        this.log = function(msg) {
            console.log(msg);
        }
    }
    else {
        this.log = function () {}
    }
};

SkraflGame.prototype.updateScores = function() {
   /* Display the current score including overtime penalty, if any */
   var displayLeft = Math.max(scoreLeft + penaltyLeft, 0);
   var displayRight = Math.max(scoreRight + penaltyRight, 0);
   this.scoreLeft.setScore(displayLeft);
   this.scoreRight.setScore(displayRight);
}

SkraflGame.prototype.updateClock = function() {
   /* Show the current remaining time for both players */
   var txt0 = calcTimeToGo(0);
   var txt1 = calcTimeToGo(1);
   clockLeft.setTime(txt0);
   clockRight.setTime(txt1);

   if (gameOver || penaltyLeft !== 0 || penaltyRight !== 0)
      // If we are applying an overtime penalty to the scores, update them in real-time
      this.updateScores();
};

SkraflGame.prototype.resetClock = function(newGameTime) {
   /* Set a new time base after receiving an update from the server */
   gameTime = newGameTime;
   gameTimeBase = new Date();
   this.updateClock();
   if (gameOver) {
      // Game over: stop updating the clock
      if (clockIval) {
         window.clearInterval(clockIval);
         clockIval = null;
      }
      // Stop blinking, if any
      this.clockLeft.setBlink(false);
      this.clockRight.setBlink(false);
   }
}

SkraflGame.prototype.showClock = function() {
   /* This is a timed game: show the clock stuff */
   this.clockLeft.setVisible(true);
   this.clockRight.setVisible(true);
   $(".clockface").css("display", "block");
   $("div.right-area").addClass("with-clock");
   $("div.chat-area").addClass("with-clock");
   $("div.twoletter-area").addClass("with-clock");
}

SkraflGame.prototype.startClock = function(igt) {
   /* Start the clock ticking - called from initSkrafl() */
   this.resetClock(igt);
   // Make sure the clock ticks reasonably regularly, once per second
   // According to Nyquist, we need a refresh interval of no more than 1/2 second
   if (!gameOver)
      clockIval = window.setInterval(updateClock, 500);
}
