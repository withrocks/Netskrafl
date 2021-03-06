/*

   Channel.js

   Utility functions for working with Firebase

   Copyright (C) 2015-2018 Miðeind ehf.
   Author: Vilhjalmur Thorsteinsson

   The GNU General Public License, version 3, applies to this software.
   For further information, see https://github.com/vthorsteinsson/Netskrafl

*/

function loginFirebase(token) {
   // Log in to Firebase using the provided custom token
   firebase.auth()
      .signInWithCustomToken(token)
      .catch(function(error) {
         console.log('Firebase login failed, error code: ', error.code);
         console.log('Error message: ', error.message);
      });
}

function initPresence(userId) {
   // Ensure that this user connection is recorded in Firebase
   var db = firebase.database();
   var connectedRef = db.ref('.info/connected');
   // Create a unique connection entry for this user
   var connectionPath = 'connection/' + userId;
   var userRef = db.ref(connectionPath).push();
   connectedRef.on('value', function(snap) {
      if (snap.val()) {
         // We're connected (or reconnected)
         // When I disconnect, remove this entry
         userRef.onDisconnect().remove();
         // Set presence
         userRef.set(true);
      }
      else
         // Unset presence
         userRef.set(false);
   });
}

function attachFirebaseListener(path, func) {
   // Attach a message listener to a Firebase path
   firebase.database()
      .ref(path)
      .on('value', function(data) {
         if (!data)
            return;
         var json = data.val();
         if (json)
            func(json);
      });
}

function detachFirebaseListener(path) {
   // Detach a message listener from a Firebase path
   firebase.database().ref(path).off();
}

