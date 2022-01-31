function blockHost(ip) {
  fetch("/blacklist/block", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " blocked");
    location.reload();
  });
}

function unblockHost(ip) {
  fetch("/blacklist/unblock", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " unblocked");
    location.reload();
  });
}


function rateLimit(ip) {
  fetch("/ratelimit/reduce", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " unblocked");
    location.reload();
  });
}

function rateReset(ip) {
  fetch("/ratelimit/reset", {
    method: "POST",
    body: JSON.stringify({ ip: ip }),
  }).then((_res) => {
    // alert("Host " + ip + " unblocked");
    location.reload();
  });
}