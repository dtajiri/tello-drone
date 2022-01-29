document.addEventListener("DOMContentLoaded", function () {
  var theCTRLs = document.querySelector(".controls");
  var theKeys = theCTRLs.querySelectorAll("[data-key]");
  var theMagnitudeEl = document.querySelector("#magnitude");
  var theAmount = document.querySelector("#amount");
  var theSnapshots = document.querySelector("#snapshot");
  var theServerRoute = "/drone_command";
  var theDetectionRoute = "/get_detection";
  

  const theSimpleCmds = ["takeoff", "land", "emergency"];
  const theRotationCmds = ["cw", "ccw"];
  const theMotionCmds = ["forward", "back", "up", "down"];
  const ROTATE_MAX = 360;
  const MOTION_MAX = 500;
  var   theMagnitude = 25;

  function sendCommand(aURL) {
    console.log("drone_command ", aURL);

    fetch(aURL, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
      .then((response) => response.json())
      .then(function (response) {
        //update your UI?
      });
  }

  theCTRLs.addEventListener(
    "click",
    function (event) {
      var theCmd = event.target.dataset.cmd;
      if (undefined === theCmd) theCmd = event.target.parentNode.dataset.cmd;
      if (undefined != theCmd) {
        // send command
        sendCommand(formatCommand(theCmd));
      }
    },
    false
  );

  function formatCommand(aCmd) {
    if (theSimpleCmds.includes(aCmd))
      var theURL = `${theServerRoute}/${aCmd}`;
    else {
      var theScale = theRotationCmds.includes(aCmd) ? ROTATE_MAX : MOTION_MAX;
      var theArg = parseInt(theScale*(theMagnitude/100));
      var theURL = `${theServerRoute}/${aCmd}/${theArg}`;
    }

    return theURL;
  }


  // Watch the snapshot button...
  theSnapshots.addEventListener("click", (event) => {
    var theDir=document.querySelector('input[name="orientation"]:checked');
    var theURL=`/snapshots/${theDir.value}`;
    console.log('url ', theURL);

    fetch(theURL)
        .then(response => response.json())
        .then(function() {
          console.log('update your images...');
          //Implement your logic here to update the images. There are two primary ways to do this...
          // 1. Have your server push image data (binary), decode it, and inject into your page (complicated)
          // 2. Use JS to change image URLS and add query string to end, to force reload of the image(s) (recommended)
          // Make sure that you delay for a little bit of time so the server has time to write the images to the public folder
          var timestamp = new Date().getTime();  
  
          var el = document.getElementById('screenshot');  
        
          var queryString = "?t=" + timestamp;    
        
          el.src = '/screenshot.jpg' + queryString;

          var delayInMilliseconds = 500; 
          setTimeout(function() {
          var timestamp = new Date().getTime();  

          var al = document.getElementById('detected');

          var queryString = "?t=" + timestamp;    
        
          al.src = '/detected_objects.jpg' + queryString; 
          }, delayInMilliseconds);   
        });

    fetch('http://localhost:8000/get_detection')
        .then(response => response.json())
        .then(function(response){
          console.log(response)
          document.getElementById("objectList").innerHTML = ''
          for (items in response){
            document.getElementById("objectList").innerHTML += response[items] + '<br>';
            }
      });
        
  });

  //watch the slider...
  theMagnitudeEl.addEventListener("input", (event) => {
    theMagnitude = parseFloat(event.target.value);
    var theDeg= parseInt(ROTATE_MAX*(theMagnitude/100));
    var theDist= parseInt(MOTION_MAX*(theMagnitude/100));
    theAmount.textContent=`(deg: ${theDeg}, move: ${theDist})`;
  });


});

function getValue() {
  var theDir=document.querySelector('input[name="orientation"]:checked');
  var isChecked = document.getElementById("slide").checked;
  var target = document.getElementById("input").value;
   
  if(isChecked){
    console.log("Input is checked");
    target = target.toLowerCase();
    console.log(target)
    console.log(theDir.value)
    route = `${theDir.value}_`+`${target}`
    console.log(route)
    fetch(`/target/${theDir.value}_`+`${target}`)
        .then(response => response.json())
  } 
  else {
    console.log("Input is NOT checked");
  }
}


