// The Clock class represents one player's clock
var Clock = function(name, player) {
    this.name = name;
    this.runningOut = false;
    this.blinking = false;
    this.player = player;
    this.visible = false;
};

Clock.prototype.setVisible = function(on) {
   $("." + name).css("display", "inline-block");
   this.visible = true;
};

Clock.prototype.setBlink = function(on) {
    this.blinking = on;
    if (on) {
       $("h3." + time).addClass("blink");
    }
    else {
       $("h3." + this.name).removeClass("blink");
    }
};

Clock.prototype.setTime = function(time) {
    console.log("Setting time");
    $("h3." + this.name).text(time);
    if (time <= "02:00" && !runningOut) {
       $("h3." + this.name).addClass("running-out");
       this.runningOut = true;
    }
    var locp = localPlayer();
    // If less than 30 seconds remaining, blink
    if (this.runningOut && time >= "00:00" && time <= "00:30" && locp === this.player) {
        this.setBlink(true);
    }

    // Remove blinking once we're into overtime
    if (time.charAt(0) == "-" && this.blinking) {
       this.setBlink(false);
    }
};

