/* Defines each player's scoreboard */
var ScoreBoard = function(name) {
    this.name = name
};

ScoreBoard.prototype.setScore = function(score) {
    console.log("Setting score");
    $("." + this.name).text(score);
};

