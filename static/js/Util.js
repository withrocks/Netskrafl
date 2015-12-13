// Generic non-application specific code
function decodeTimestamp(ts) {
   // Parse and split a timestamp string from the format YYYY-MM-DD HH:MM:SS
   return {
      year: parseInt(ts.substr(0, 4)),
      month: parseInt(ts.substr(5, 2)),
      day: parseInt(ts.substr(8, 2)),
      hour: parseInt(ts.substr(11, 2)),
      minute: parseInt(ts.substr(14, 2)),
      second: parseInt(ts.substr(17, 2))
   };
}

function timeDiff(dtFrom, dtTo) {
   // Return the difference between two JavaScript time points, in seconds
   return Math.round((dtTo - dtFrom) / 1000.0);
}

function escapeHtml(string) {
   /* Utility function to properly encode a string into HTML */
   return String(string).replace(/[&<>"'\/]/g, function (s) {
      return entityMap[s];
   });
}

function arrayEqual(a, b) {
   /* Return true if arrays a and b are equal */
   if (a.length != b.length)
      return false;
   for (var i = 0; i < a.length; i++)
      if (a[i] != b[i])
         return false;
   return true;
}

function nullFunc(json) {
   /* Null placeholder function to use for Ajax queries that don't need a success func */
}

function nullCompleteFunc(xhr, status) {
   /* Null placeholder function for Ajax completion */
}

function errFunc(xhr, status, errorThrown) {
   /* Default error handling function for Ajax communications */
   // alert("Villa í netsamskiptum");
   console.log("Error: " + errorThrown);
   console.log("Status: " + status);
   console.dir(xhr);
}

function serverQuery(requestUrl, jsonData, successFunc, completeFunc, errorFunc) {
   /* Wraps a simple, standard Ajax request to the server */
   $.ajax({
      // The URL for the request
      url: requestUrl,

      // The data to send
      data: jsonData,

      // Whether this is a POST or GET request
      type: "POST",

      // The type of data we expect back
      dataType : "json",

      cache: false,

      // Code to run if the request succeeds;
      // the response is passed to the function
      success: (!successFunc) ? nullFunc : successFunc,

      // Code to run if the request fails; the raw request and
      // status codes are passed to the function
      error: (!errorFunc) ? errFunc : errorFunc,

      // code to run regardless of success or failure
      complete: (!completeFunc) ? nullCompleteFunc : completeFunc
   });
}

function reloadPage() {
   /* Reload this page from the server */
   window.location.reload(true); // Bypass cache
}

